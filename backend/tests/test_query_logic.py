"""Tests for nl_query.py's deterministic, non-LLM logic: filter
sanitization, metro resolution, the median_rent -> median_gross_rent
fallback, the rent_to_income_pct computation, and explain_filters' text.

These are the pieces the eval suite only exercises *indirectly* (through
whatever filters DeepSeek happens to produce for a given prompt) - a bug
here could hide behind "the LLM picked a reasonable filter" without ever
being tested against a deliberately-constructed edge case. That gap is
exactly what these tests close.
"""

from datetime import date

from app.nl_query import (
    _fetch_income,
    _fetch_rent_rows,
    _parse_period,
    _resolve_metro,
    _sanitize_filters,
    explain_filters,
    run_market_query,
    source_citation,
    summarize_metric_facts,
)
from app.models import MetricSource, Metro, NationalMetric
from app.schemas import MarketMetricPoint, MarketQueryFilters, MetricName
from tests.conftest import GAPFORD_GROSS_RENT, TESTVILLE_INCOME, TESTVILLE_RENT_FEB, TESTVILLE_RENT_JAN


# --- _sanitize_filters ---


def test_sanitize_clears_bed_size_for_non_rent_metric():
    filters = MarketQueryFilters(metric=MetricName.VACANCY_RATE, bed_size="overall")
    assert _sanitize_filters(filters).bed_size is None


def test_sanitize_keeps_bed_size_for_median_rent():
    filters = MarketQueryFilters(metric=MetricName.MEDIAN_RENT, bed_size="2br")
    assert _sanitize_filters(filters).bed_size == "2br"


def test_sanitize_clears_bed_size_for_rent_to_income():
    # rent_to_income_pct always uses "overall" internally - a stale
    # bed_size from a prior turn must not leak into it.
    filters = MarketQueryFilters(metric=MetricName.RENT_TO_INCOME_PCT, bed_size="1br")
    assert _sanitize_filters(filters).bed_size is None


def test_sanitize_is_a_noop_when_nothing_to_clear():
    filters = MarketQueryFilters(metric=MetricName.MEDIAN_SALE_PRICE, bed_size=None)
    assert _sanitize_filters(filters) == filters


# --- _resolve_metro ---


def test_resolve_metro_exact_match(seeded_db):
    metros = [seeded_db.get(Metro, "testville-ts")]
    assert _resolve_metro("Testville, TS", metros).id == "testville-ts"


def test_resolve_metro_city_substring_match(seeded_db):
    metros = list(seeded_db.query(Metro).all())
    assert _resolve_metro("testville", metros).id == "testville-ts"


def test_resolve_metro_no_match_returns_none(seeded_db):
    metros = list(seeded_db.query(Metro).all())
    assert _resolve_metro("Nowhereville", metros) is None


# --- _parse_period ---


def test_parse_period_valid():
    assert _parse_period("2024-03") == date(2024, 3, 1)


def test_parse_period_none_input():
    assert _parse_period(None) is None


def test_parse_period_empty_string():
    assert _parse_period("") is None


# --- median_rent -> median_gross_rent fallback (_fetch_rent_rows) ---


def test_fetch_rent_rows_real_data_no_fallback(seeded_db):
    metro = seeded_db.get(Metro, "testville-ts")
    rows, used_fallback = _fetch_rent_rows(seeded_db, metro, "overall", None, None)
    assert used_fallback is False
    assert [r.value for r in rows] == [TESTVILLE_RENT_JAN, TESTVILLE_RENT_FEB]


def test_fetch_rent_rows_falls_back_for_gap_metro(seeded_db):
    metro = seeded_db.get(Metro, "gapford-gf")
    rows, used_fallback = _fetch_rent_rows(seeded_db, metro, None, None, None)
    assert used_fallback is True
    assert len(rows) == 1
    assert rows[0].value == GAPFORD_GROSS_RENT
    assert rows[0].metric == "median_gross_rent"  # never relabeled as median_rent


def test_fetch_rent_rows_no_fallback_when_bed_size_specific(seeded_db):
    # Census gross rent has no bed-size breakdown - a 1BR-specific
    # question about a gap metro must NOT silently get the overall figure.
    metro = seeded_db.get(Metro, "gapford-gf")
    rows, used_fallback = _fetch_rent_rows(seeded_db, metro, "1br", None, None)
    assert rows == []
    assert used_fallback is False


def test_fetch_rent_rows_no_data_when_no_fallback_exists(seeded_db):
    metro = seeded_db.get(Metro, "emptyburg-eb")
    rows, used_fallback = _fetch_rent_rows(seeded_db, metro, None, None, None)
    assert rows == []
    assert used_fallback is False


# --- _fetch_income ---


def test_fetch_income_present(seeded_db):
    metro = seeded_db.get(Metro, "testville-ts")
    assert _fetch_income(seeded_db, metro) == TESTVILLE_INCOME


def test_fetch_income_genuine_gap(seeded_db):
    # Gapford has the rent fallback but NOT income - a narrower gap than
    # gross rent, deliberately not filled in (see ingest_market_data.py).
    metro = seeded_db.get(Metro, "gapford-gf")
    assert _fetch_income(seeded_db, metro) is None


# --- run_market_query: median_rent, trend + ranking modes ---


def test_run_market_query_trend_normal_metro(seeded_db):
    filters = MarketQueryFilters(metros=["Testville, TS"], metric=MetricName.MEDIAN_RENT, bed_size="overall")
    points, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    assert [p.value for p in points] == [TESTVILLE_RENT_JAN, TESTVILLE_RENT_FEB]
    assert unmatched == no_data == approximated == []


def test_run_market_query_trend_gap_metro_uses_fallback(seeded_db):
    filters = MarketQueryFilters(metros=["Gapford, GF"], metric=MetricName.MEDIAN_RENT)
    points, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    assert len(points) == 1 and points[0].value == GAPFORD_GROSS_RENT
    assert approximated == ["Gapford, GF"]
    assert no_data == []


def test_run_market_query_trend_no_data_and_unmatched(seeded_db):
    filters = MarketQueryFilters(metros=["Emptyburg, EB", "Nowhereville"], metric=MetricName.MEDIAN_RENT)
    points, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    assert points == []
    assert unmatched == ["Nowhereville"]
    assert no_data == ["Emptyburg, EB"]
    assert approximated == []


def test_run_market_query_ranking_mode_all_metros_skips_gaps_silently(seeded_db):
    # Ranking mode with no metros named means "all of them" - a metro with
    # zero data (even the fallback) is silently excluded from the ranking,
    # not reported as no_data, matching the existing design for every
    # other metric (no_data_metros is only populated for explicitly named
    # metros in ranking mode).
    filters = MarketQueryFilters(metros=[], metric=MetricName.MEDIAN_RENT, sort_by="value", sort_order="desc")
    points, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    metro_names = {p.metro for p in points}
    assert metro_names == {"Testville, TS", "Gapford, GF"}
    assert "Emptyburg, EB" not in metro_names
    assert no_data == []
    assert approximated == ["Gapford, GF"]


def test_run_market_query_change_mode_ranks_by_pct_change_not_latest_value(seeded_db):
    # The bug this mode exists to fix: "which metros are growing fastest"
    # must rank by rate of change, not by whoever happens to have the
    # highest latest value. Gapford's single gross-rent fallback point
    # and Emptyburg's complete absence of rent data both have nothing to
    # compute a change from, so only Testville (two real rent periods)
    # qualifies for an unnamed-metros ranking.
    # bed_size pinned to "overall" - left unset, Testville's 1br row
    # would mix into the same series (see _query_metric_rows, which
    # doesn't filter by bed_size when it's None), which is a real,
    # separate behavior this test isn't about.
    filters = MarketQueryFilters(
        metros=[], metric=MetricName.MEDIAN_RENT, bed_size="overall", sort_by="change", sort_order="desc"
    )
    points, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    assert [p.metro for p in points] == ["Testville, TS"]
    expected_pct = (TESTVILLE_RENT_FEB - TESTVILLE_RENT_JAN) / TESTVILLE_RENT_JAN * 100
    assert points[0].value == expected_pct
    assert no_data == []
    assert approximated == []


def test_run_market_query_change_mode_no_data_for_single_snapshot_metric(seeded_db):
    # median_household_income has exactly one row for Testville - there's
    # no second point to compute a rate of change from, so an explicitly
    # named metro must come back as a genuine no_data case, not a crash
    # or a nonsense 0% change.
    filters = MarketQueryFilters(metros=["Testville, TS"], metric=MetricName.MEDIAN_HOUSEHOLD_INCOME, sort_by="change")
    points, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    assert points == []
    assert no_data == ["Testville, TS"]


# --- run_market_query: median_household_income ---


def test_run_market_query_income_present(seeded_db):
    filters = MarketQueryFilters(metros=["Testville, TS"], metric=MetricName.MEDIAN_HOUSEHOLD_INCOME)
    points, _, no_data, _ = run_market_query(seeded_db, filters)
    assert len(points) == 1 and points[0].value == TESTVILLE_INCOME
    assert no_data == []


def test_run_market_query_income_genuine_gap(seeded_db):
    filters = MarketQueryFilters(metros=["Gapford, GF"], metric=MetricName.MEDIAN_HOUSEHOLD_INCOME)
    points, _, no_data, _ = run_market_query(seeded_db, filters)
    assert points == []
    assert no_data == ["Gapford, GF"]


# --- run_market_query: rent_to_income_pct ---


def test_rent_to_income_pct_computation_is_exact(seeded_db):
    filters = MarketQueryFilters(metros=["Testville, TS"], metric=MetricName.RENT_TO_INCOME_PCT)
    points, _, no_data, _ = run_market_query(seeded_db, filters)
    expected_jan = (TESTVILLE_RENT_JAN * 12 / TESTVILLE_INCOME) * 100
    expected_feb = (TESTVILLE_RENT_FEB * 12 / TESTVILLE_INCOME) * 100
    assert [p.value for p in points] == [expected_jan, expected_feb]
    assert no_data == []


def test_rent_to_income_pct_no_data_when_income_missing_even_with_rent_fallback(seeded_db):
    # Gapford has rent (via fallback) but no income at all - the ratio
    # genuinely can't be computed, and must not silently drop the income
    # term or guess at it.
    filters = MarketQueryFilters(metros=["Gapford, GF"], metric=MetricName.RENT_TO_INCOME_PCT)
    points, _, no_data, approximated = run_market_query(seeded_db, filters)
    assert points == []
    assert no_data == ["Gapford, GF"]
    assert approximated == []


def test_rent_to_income_pct_no_data_when_rent_missing(seeded_db):
    filters = MarketQueryFilters(metros=["Emptyburg, EB"], metric=MetricName.RENT_TO_INCOME_PCT)
    points, _, no_data, _ = run_market_query(seeded_db, filters)
    assert points == []
    assert no_data == ["Emptyburg, EB"]


def test_rent_to_income_pct_ranking_mode(seeded_db):
    filters = MarketQueryFilters(metros=[], metric=MetricName.RENT_TO_INCOME_PCT, sort_by="value", sort_order="desc")
    points, _, no_data, _ = run_market_query(seeded_db, filters)
    # Only Testville has both legs - Gapford (no income) and Emptyburg (no
    # rent) are silently excluded from an unnamed-metros ranking, same
    # convention as every other metric.
    assert [p.metro for p in points] == ["Testville, TS"]


# --- explain_filters ---


def test_explain_filters_names_the_specific_county(seeded_db):
    filters = MarketQueryFilters(metros=["Gapford, GF"], metric=MetricName.MEDIAN_RENT)
    _, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    text = explain_filters(filters, unmatched, no_data, approximated, seeded_db)
    assert "Gapford, GF (Gap County, GF)" in text
    assert "Census ACS median gross rent" in text


def test_explain_filters_surfaces_no_data(seeded_db):
    filters = MarketQueryFilters(metros=["Emptyburg, EB"], metric=MetricName.MEDIAN_RENT)
    _, unmatched, no_data, approximated = run_market_query(seeded_db, filters)
    text = explain_filters(filters, unmatched, no_data, approximated, seeded_db)
    assert "No median rent data available for: Emptyburg, EB" in text


def test_explain_filters_surfaces_unmatched():
    filters = MarketQueryFilters(metros=["Nowhereville"], metric=MetricName.MEDIAN_SALE_PRICE)
    text = explain_filters(filters, ["Nowhereville"], [], [], None)
    assert "Couldn't find a tracked metro matching: Nowhereville" in text


def test_explain_filters_change_mode_names_percent_change_not_plain_ranking():
    filters = MarketQueryFilters(metros=[], metric=MetricName.MEDIAN_RENT, sort_by="change", sort_order="desc")
    text = explain_filters(filters, [], [], [], None)
    assert "ranked by percent change, desc" in text
    assert "across all metros" in text


def test_explain_filters_surfaces_unsupported_aspects():
    filters = MarketQueryFilters(
        metros=["Testville, TS"], metric=MetricName.MEDIAN_SALE_PRICE, unsupported_aspects=["school quality"]
    )
    text = explain_filters(filters, [], [], [], None)
    assert "This system can't evaluate: school quality." in text


# --- source_citation ---


def test_source_citation_names_the_real_source():
    filters = MarketQueryFilters(metros=["Austin, TX"], metric=MetricName.MEDIAN_SALE_PRICE)
    assert source_citation(filters, []) == "Redfin"


def test_source_citation_notes_the_census_fallback_when_actually_used():
    # A plain median_rent query is Apartment List - but one that actually
    # fell back to Census gross rent for some metros is partly sourced
    # from Census too, and citing only Apartment List would misattribute
    # the number a reader is looking at.
    filters = MarketQueryFilters(metros=["Gapford, GF"], metric=MetricName.MEDIAN_RENT)
    text = source_citation(filters, ["Gapford, GF"])
    assert "Apartment List" in text
    assert "Census ACS gross rent" in text


def test_source_citation_is_plain_apartment_list_without_a_fallback():
    filters = MarketQueryFilters(metros=["Austin, TX"], metric=MetricName.MEDIAN_RENT)
    assert source_citation(filters, []) == "Apartment List"


# --- National metrics (Freddie Mac mortgage rates - no metro dimension) ---


def _add_pmms(db, metric, period, value):
    db.add(NationalMetric(period=period, source=MetricSource.FREDDIE_MAC, metric=metric, value=value))


def test_sanitize_clears_metros_for_national_metric():
    filters = MarketQueryFilters(metros=["Austin, TX"], metric=MetricName.MORTGAGE_RATE_30YR_FIXED)
    assert _sanitize_filters(filters).metros == []


def test_national_query_trend_ignores_metros_entirely(db_session):
    _add_pmms(db_session, "mortgage_rate_30yr_fixed", date(2024, 1, 5), 6.62)
    _add_pmms(db_session, "mortgage_rate_30yr_fixed", date(2024, 1, 12), 6.66)
    _add_pmms(db_session, "mortgage_rate_15yr_fixed", date(2024, 1, 5), 5.89)  # different metric, must be excluded
    db_session.commit()

    filters = MarketQueryFilters(metric=MetricName.MORTGAGE_RATE_30YR_FIXED)
    points, unmatched, no_data, approximated = run_market_query(db_session, filters)
    assert [p.value for p in points] == [6.62, 6.66]
    assert all(p.metro == "United States" for p in points)
    assert unmatched == no_data == approximated == []


def test_national_query_ranking_mode_returns_latest_single_point(db_session):
    _add_pmms(db_session, "mortgage_rate_30yr_fixed", date(2024, 1, 5), 6.62)
    _add_pmms(db_session, "mortgage_rate_30yr_fixed", date(2024, 1, 12), 6.66)
    db_session.commit()

    filters = MarketQueryFilters(metric=MetricName.MORTGAGE_RATE_30YR_FIXED, sort_by="value")
    points, *_ = run_market_query(db_session, filters)
    assert len(points) == 1
    assert points[0].period == date(2024, 1, 12)
    assert points[0].value == 6.66


def test_national_query_no_data_when_range_excludes_everything(db_session):
    _add_pmms(db_session, "mortgage_rate_30yr_fixed", date(2024, 1, 5), 6.62)
    db_session.commit()

    filters = MarketQueryFilters(metric=MetricName.MORTGAGE_RATE_30YR_FIXED, start_period="2030-01")
    points, unmatched, no_data, approximated = run_market_query(db_session, filters)
    assert points == []
    assert no_data == ["United States"]


def test_explain_filters_national_trend_has_no_metro_language(db_session):
    _add_pmms(db_session, "mortgage_rate_30yr_fixed", date(2024, 1, 5), 6.62)
    db_session.commit()
    filters = MarketQueryFilters(metric=MetricName.MORTGAGE_RATE_30YR_FIXED)
    _, unmatched, no_data, approximated = run_market_query(db_session, filters)
    text = explain_filters(filters, unmatched, no_data, approximated, db_session)
    assert text == "Showing 30-year fixed mortgage rate."
    assert "no metro specified" not in text.lower()


def test_explain_filters_national_ranking_has_no_ranking_language(db_session):
    _add_pmms(db_session, "mortgage_rate_30yr_fixed", date(2024, 1, 5), 6.62)
    db_session.commit()
    filters = MarketQueryFilters(metric=MetricName.MORTGAGE_RATE_30YR_FIXED, sort_by="value")
    _, unmatched, no_data, approximated = run_market_query(db_session, filters)
    text = explain_filters(filters, unmatched, no_data, approximated, db_session)
    # Ranking mode is meaningless for a single national series - must not
    # claim to be ranking across metros that were never involved.
    assert "across all metros" not in text
    assert "ranked" not in text


# --- summarize_metric_facts ---
# Same cases as frontend/src/analysis.test.ts's summarizeResults - this is
# a deliberate Python port of that same deterministic logic (see
# summarize_metric_facts' docstring), so it's tested the same way.


def _point(metro: str, period: str, value: float) -> MarketMetricPoint:
    return MarketMetricPoint(metro=metro, period=date.fromisoformat(period), value=value)


def test_summarize_metric_facts_empty():
    assert summarize_metric_facts([], MetricName.MEDIAN_SALE_PRICE, "period") == ""


def test_summarize_metric_facts_ranking_single_point():
    text = summarize_metric_facts(
        [_point("Austin, TX", "2026-08-01", 450000)], MetricName.MEDIAN_SALE_PRICE, "value"
    )
    assert text == "Austin, TX: $450,000."


def test_summarize_metric_facts_ranking_multiple_points():
    points = [
        _point("Miami, FL", "2026-08-01", 28.4),
        _point("Boston, MA", "2026-08-01", 23.5),
        _point("Austin, TX", "2026-08-01", 20.1),
    ]
    text = summarize_metric_facts(points, MetricName.RENT_TO_INCOME_PCT, "value")
    assert text == "Miami, FL leads at 28.4%; Austin, TX is lowest at 20.1%."


def test_summarize_metric_facts_change_single_point():
    text = summarize_metric_facts([_point("Austin, TX", "2026-08-01", 27.3)], MetricName.MEDIAN_RENT, "change")
    assert text == "Austin, TX: up 27.3%."


def test_summarize_metric_facts_change_multiple_points():
    points = [
        _point("Austin, TX", "2026-08-01", 27.3),
        _point("Miami, FL", "2026-08-01", -4.2),
    ]
    text = summarize_metric_facts(points, MetricName.MEDIAN_RENT, "change")
    assert text == "Austin, TX has the biggest change at +27.3%; Miami, FL has the smallest change at -4.2%."


def test_summarize_metric_facts_trend_single_period():
    text = summarize_metric_facts([_point("Denver, CO", "2026-08-01", 2000)], MetricName.MEDIAN_RENT, "period")
    assert text == "Denver, CO: $2,000."


def test_summarize_metric_facts_trend_direction_and_pct_change():
    points = [_point("Denver, CO", "2024-01-01", 2000), _point("Denver, CO", "2024-02-01", 2200)]
    text = summarize_metric_facts(points, MetricName.MEDIAN_RENT, "period")
    assert text == "Denver, CO: $2,000 -> $2,200 (up 10.0%)."


def test_summarize_metric_facts_calls_out_real_peak():
    points = [
        _point("Denver, CO", "2024-01-01", 2000),
        _point("Denver, CO", "2024-02-01", 2500),
        _point("Denver, CO", "2024-03-01", 2100),
    ]
    text = summarize_metric_facts(points, MetricName.MEDIAN_RENT, "period")
    assert "peaked at $2,500 in Feb 2024" in text


def test_summarize_metric_facts_near_zero_change_is_flat():
    points = [_point("Denver, CO", "2024-01-01", 2000), _point("Denver, CO", "2024-02-01", 2000.5)]
    text = summarize_metric_facts(points, MetricName.MEDIAN_RENT, "period")
    assert "(flat" in text


def test_summarize_metric_facts_handles_multiple_metros_independently():
    points = [
        _point("Austin, TX", "2024-01-01", 400000),
        _point("Austin, TX", "2024-02-01", 420000),
        _point("Denver, CO", "2024-01-01", 500000),
        _point("Denver, CO", "2024-02-01", 480000),
    ]
    text = summarize_metric_facts(points, MetricName.MEDIAN_SALE_PRICE, "period")
    assert "Austin, TX: $400,000 -> $420,000 (up 5.0%)." in text
    assert "Denver, CO: $500,000 -> $480,000 (down 4.0%)." in text
