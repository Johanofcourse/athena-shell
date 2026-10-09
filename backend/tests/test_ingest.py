"""ETL tests for ingest_market_data.py, run against tiny fixture CSVs
(written to tmp_path, never the real 121k-row files) so parsing logic and
crosswalk-driven joins are checked in isolation, fast, and deterministically.

Uses monkeypatch to point the module's DATA_DIR and file-list constants at
fixture files instead of the real data/samples/ directory - the ingest
functions themselves are exercised unmodified.
"""

import csv
import json
from datetime import date

from app import ingest_market_data as ingest
from app import ingest_national_data as ingest_national
from app.models import MarketMetric, MetricSource, Metro, NationalMetric


def _write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def _write_census_csv(path, header, data_row):
    # utf-8-sig to match the real Census export's BOM, which is why
    # _parse_census_row opens with that encoding specifically.
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(data_row)


# --- pure helpers ---


def test_normalize_aptlist_name_strips_suffix():
    assert ingest._normalize_aptlist_name("Testville, TS Metro Area") == "Testville, TS"


def test_normalize_aptlist_name_leaves_bare_name_alone():
    assert ingest._normalize_aptlist_name("Testville, TS") == "Testville, TS"


def test_parse_float_valid():
    assert ingest._parse_float("1234.5") == 1234.5


def test_parse_float_blank_and_none():
    assert ingest._parse_float("") is None
    assert ingest._parse_float("   ") is None
    assert ingest._parse_float(None) is None


def test_parse_float_invalid_string():
    assert ingest._parse_float("N/A") is None


def test_parse_census_row(tmp_path):
    path = tmp_path / "census.csv"
    _write_census_csv(
        path,
        [
            "Label (Grouping)",
            "Fake County, ST!!Estimate",
            "Fake County, ST!!Margin of Error",
            "Other County, ST!!Estimate",
            "Other County, ST!!Margin of Error",
            "Blank County, ST!!Estimate",
            "Blank County, ST!!Margin of Error",
        ],
        ["Median gross rent", "1,500", "±20", "2,000", "±30", "", "±0"],
    )
    values = ingest._parse_census_row(path)
    assert values == {"Fake County, ST": 1500.0, "Other County, ST": 2000.0}
    assert "Blank County, ST" not in values


# --- load_metros (against the real crosswalk - a real integration check) ---


def test_load_metros_creates_all_fifty_and_matches_crosswalk_fields(db_session):
    redfin_to_id, aptlist_to_id, income_to_id = ingest.load_metros(db_session)
    assert db_session.query(Metro).count() == 50
    assert len(redfin_to_id) == 50
    assert len(aptlist_to_id) == 40  # 10 metro-division gaps excluded
    assert len(income_to_id) == 40

    anaheim = db_session.get(Metro, "anaheim-ca")
    assert anaheim.canonical_name == "Anaheim, CA"
    assert anaheim.aptlist_name is None
    assert anaheim.census_income_name is None

    austin = db_session.get(Metro, "austin-tx")
    assert austin.aptlist_name == "Austin-Round Rock-Georgetown, TX"


def test_load_metros_is_idempotent(db_session):
    ingest.load_metros(db_session)
    ingest.load_metros(db_session)
    assert db_session.query(Metro).count() == 50


# --- ingest_redfin ---


def test_ingest_redfin_filters_by_region_type_and_known_metro(db_session, monkeypatch, tmp_path):
    db_session.add(Metro(id="testville-ts", canonical_name="Testville, TS", state="TS"))
    db_session.commit()

    path = tmp_path / "redfin.csv"
    _write_csv(
        path,
        ["REGION TYPE", "REGION NAME", "PERIOD BEGIN", "MEDIAN SALE PRICE NSA ($)", "HOMES SOLD"],
        [
            ("Metro", "Testville, TS metro area", "2024-01-01", "300000", "120"),
            ("State", "Testville, TS metro area", "2024-01-01", "111111", "10"),  # wrong region type
            ("Metro", "Unknown Place metro area", "2024-01-01", "222222", "20"),  # unmatched metro
            ("Metro", "Testville, TS metro area", "2024-02-01", "", "130"),  # blank price, real homes_sold
        ],
    )
    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        ingest,
        "REDFIN_FILES",
        [("redfin.csv", {"MEDIAN SALE PRICE NSA ($)": "median_sale_price", "HOMES SOLD": "homes_sold"})],
    )

    count = ingest.ingest_redfin(db_session, {"Testville, TS metro area": "testville-ts"})
    db_session.commit()
    assert count == 3  # Jan: 2 metrics, Feb: 1 metric (blank price skipped)

    rows = db_session.query(MarketMetric).filter_by(metro_id="testville-ts").all()
    by_metric_period = {(r.metric, r.period): r.value for r in rows}
    assert by_metric_period[("median_sale_price", date(2024, 1, 1))] == 300000.0
    assert by_metric_period[("homes_sold", date(2024, 1, 1))] == 120.0
    assert by_metric_period[("homes_sold", date(2024, 2, 1))] == 130.0
    assert ("median_sale_price", date(2024, 2, 1)) not in by_metric_period


# --- ingest_apartment_list ---


def test_ingest_apartment_list_handles_bed_size_split_and_name_suffix_inconsistency(
    db_session, monkeypatch, tmp_path
):
    db_session.add(Metro(id="testville-ts", canonical_name="Testville, TS", state="TS"))
    db_session.commit()

    rent_path = tmp_path / "rent.csv"
    _write_csv(
        rent_path,
        ["location_name", "location_type", "bed_size", "2024_01", "2024_02"],
        [
            ("Testville, TS", "Metro", "overall", "2000", "2100"),
            ("Testville, TS", "Metro", "1br", "1500", "1550"),
            ("Testville, TS", "County", "overall", "999", "999"),  # wrong location_type
            ("Unknown Place", "Metro", "overall", "111", "111"),  # unmatched metro
        ],
    )
    # Regression fixture for the real bug: this file suffixes every name
    # with " Metro Area" like the real Time on Market file did, and has no
    # bed_size column at all.
    tom_path = tmp_path / "time_on_market.csv"
    _write_csv(
        tom_path,
        ["location_name", "location_type", "2024_01"],
        [("Testville, TS Metro Area", "Metro", "45")],
    )

    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        ingest,
        "APARTMENT_LIST_FILES",
        [("rent.csv", "median_rent", True), ("time_on_market.csv", "time_on_market_days", False)],
    )

    count = ingest.ingest_apartment_list(db_session, {"Testville, TS": "testville-ts"})
    db_session.commit()
    assert count == 5  # 2 overall + 2 1br + 1 time-on-market

    rows = db_session.query(MarketMetric).filter_by(metro_id="testville-ts").all()
    rent_overall = [r for r in rows if r.metric == "median_rent" and r.bed_size == "overall"]
    rent_1br = [r for r in rows if r.metric == "median_rent" and r.bed_size == "1br"]
    tom_rows = [r for r in rows if r.metric == "time_on_market_days"]

    assert {r.value for r in rent_overall} == {2000.0, 2100.0}
    assert {r.value for r in rent_1br} == {1500.0, 1550.0}
    assert len(tom_rows) == 1
    assert tom_rows[0].value == 45.0
    assert tom_rows[0].bed_size is None


# --- ingest_census_income ---


def test_ingest_census_income(db_session, monkeypatch, tmp_path):
    db_session.add(Metro(id="testville-ts", canonical_name="Testville, TS", state="TS"))
    db_session.commit()

    path = tmp_path / "income.csv"
    _write_census_csv(
        path,
        [
            "Label (Grouping)",
            "Testville, TS Metro Area!!Estimate",
            "Testville, TS Metro Area!!Margin of Error",
            "Unmapped Place, ZZ Metro Area!!Estimate",
            "Unmapped Place, ZZ Metro Area!!Margin of Error",
        ],
        ["Median household income", "100,431", "±1,000", "50,000", "±500"],
    )
    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ingest, "CENSUS_INCOME_FILE", "income.csv")

    count = ingest.ingest_census_income(db_session, {"Testville, TS Metro Area": "testville-ts"})
    db_session.commit()
    assert count == 1

    row = db_session.query(MarketMetric).filter_by(metro_id="testville-ts").one()
    assert row.metric == "median_household_income"
    assert row.source == MetricSource.CENSUS
    assert row.value == 100431.0
    assert row.bed_size is None
    assert row.period == ingest.CENSUS_ACS_PERIOD


# --- ingest_census_gross_rent_fallback ---


def test_ingest_census_gross_rent_fallback_sets_metric_and_county(db_session, monkeypatch, tmp_path):
    db_session.add(Metro(id="gapford-gf", canonical_name="Gapford, GF", state="GF"))
    db_session.commit()

    path = tmp_path / "gross_rent.csv"
    _write_census_csv(
        path,
        ["Label (Grouping)", "Gap County, GF!!Estimate", "Gap County, GF!!Margin of Error"],
        ["Median gross rent", "1,800", "±15"],
    )
    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ingest, "CENSUS_GROSS_RENT_GAP_FILES", [("gross_rent.csv", {"Gap County, GF": "gapford-gf"})])

    count = ingest.ingest_census_gross_rent_fallback(db_session)
    db_session.commit()
    assert count == 1

    row = db_session.query(MarketMetric).filter_by(metro_id="gapford-gf").one()
    assert row.metric == "median_gross_rent"
    assert row.source == MetricSource.CENSUS
    assert row.value == 1800.0

    # The feature the caveat-specificity follow-up depends on: the metro
    # itself gets tagged with which county backs the number.
    metro = db_session.get(Metro, "gapford-gf")
    assert metro.census_gross_rent_county == "Gap County, GF"


# --- ingest_national_data (Freddie Mac PMMS - no metro dimension) ---


def test_ingest_pmms_parses_three_series_and_skips_blanks(db_session, monkeypatch, tmp_path):
    path = tmp_path / "pmms.csv"
    _write_csv(
        path,
        ["date", "pmms30", "pmms30p", "pmms15", "pmms15p", "pmms51", "pmms51p", "pmms51m", "pmms51spread"],
        [
            # Mirrors the real file: pmms15/pmms51 genuinely start blank
            # before Freddie Mac began surveying them.
            ("4/2/1971", "7.33", " ", "", "", "", "", "", ""),
            ("8/30/1991", "9.15", "1.9", "8.77", "1.9", "", "", "", ""),
            ("1/6/2005", "5.77", "0.7", "5.21", "0.6", "5.03", "0.5", "2.78", ""),
        ],
    )
    monkeypatch.setattr(ingest_national, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ingest_national, "PMMS_FILE", "pmms.csv")

    count = ingest_national.ingest_pmms(db_session)
    db_session.commit()
    assert count == 1 + 2 + 3  # row1: only pmms30; row2: +pmms15; row3: +pmms51

    rows = db_session.query(NationalMetric).all()
    assert all(r.source == MetricSource.FREDDIE_MAC for r in rows)

    thirty_yr = {r.period: r.value for r in rows if r.metric == "mortgage_rate_30yr_fixed"}
    assert thirty_yr == {date(1971, 4, 2): 7.33, date(1991, 8, 30): 9.15, date(2005, 1, 6): 5.77}

    fifteen_yr = {r.period: r.value for r in rows if r.metric == "mortgage_rate_15yr_fixed"}
    assert fifteen_yr == {date(1991, 8, 30): 8.77, date(2005, 1, 6): 5.21}

    arm = {r.period: r.value for r in rows if r.metric == "mortgage_rate_5_1_arm"}
    assert arm == {date(2005, 1, 6): 5.03}

    # Points/margin/spread columns are deliberately not ingested at all.
    assert not any("p" in r.metric or "spread" in r.metric or "margin" in r.metric for r in rows)


# --- ingest_bls_unemployment (live-API source, offline-parsed from a saved JSON) ---


def test_ingest_bls_unemployment_parses_response_and_maps_area_codes_to_metros(db_session, monkeypatch, tmp_path):
    db_session.add(Metro(id="testville-ts", canonical_name="Testville, TS", state="TS"))
    db_session.commit()

    # Mirrors the real BLS API response shape (series_id = "LAU" + area
    # code + 2-digit measure code), including a blank value (BLS uses
    # this for suppressed/unavailable data points) and a series whose
    # area code isn't in our crosswalk at all (must be silently skipped,
    # not error - the real response covers exactly our 50 metros, but
    # nothing structurally guarantees that stays true forever).
    payload = {
        "Results": {
            "series": [
                {
                    "seriesID": "LAUXX000000000000003",
                    "data": [
                        {"year": "2024", "period": "M01", "value": "4.5"},
                        {"year": "2024", "period": "M02", "value": "4.2"},
                        {"year": "2024", "period": "M03", "value": ""},
                    ],
                },
                {
                    "seriesID": "LAUYY999999999999903",
                    "data": [{"year": "2024", "period": "M01", "value": "9.9"}],
                },
            ]
        }
    }
    path = tmp_path / "bls.json"
    path.write_text(json.dumps(payload))

    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ingest, "BLS_UNEMPLOYMENT_FILE", "bls.json")
    monkeypatch.setattr(ingest, "BLS_AREA_CODES", {"testville-ts": "XX0000000000000"})

    count = ingest.ingest_bls_unemployment(db_session)
    db_session.commit()
    assert count == 2  # the blank March value and the unmapped series are both skipped

    rows = db_session.query(MarketMetric).filter_by(metro_id="testville-ts").all()
    assert {(r.period, r.value) for r in rows} == {(date(2024, 1, 1), 4.5), (date(2024, 2, 1), 4.2)}
    assert all(r.metric == "unemployment_rate" and r.source == MetricSource.BLS for r in rows)


def test_ingest_bls_unemployment_missing_file_returns_zero_without_erroring(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ingest, "BLS_UNEMPLOYMENT_FILE", "does_not_exist.json")
    assert ingest.ingest_bls_unemployment(db_session) == 0


# --- ingest_fhfa_hpi (live-API source, offline-parsed from a saved JSON) ---


def test_ingest_fhfa_hpi_parses_response_and_skips_blanks_and_unmapped_metros(db_session, monkeypatch, tmp_path):
    db_session.add(Metro(id="testville-ts", canonical_name="Testville, TS", state="TS"))
    db_session.commit()

    # Mirrors fetch_fred_house_price_index.py's saved shape: keyed by
    # metro_id (not seriesID, unlike BLS - FRED's per-series endpoint
    # doesn't echo the series ID back in each observation the way BLS's
    # batch endpoint does).
    payload = {
        "testville-ts": {
            "series_id": "ATNHPIUS00000Q",
            "observations": [
                {"date": "2024-01-01", "value": "310.5"},
                {"date": "2024-04-01", "value": "."},  # FRED's own missing-value marker
                {"date": "2024-07-01", "value": "315.2"},
            ],
        },
        "not-a-real-metro": {
            "series_id": "ATNHPIUS99999Q",
            "observations": [{"date": "2024-01-01", "value": "100.0"}],
        },
    }
    path = tmp_path / "fhfa.json"
    path.write_text(json.dumps(payload))

    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ingest, "FHFA_HPI_FILE", "fhfa.json")
    monkeypatch.setattr(ingest, "FHFA_HPI_SERIES_IDS", {"testville-ts": "ATNHPIUS00000Q"})

    count = ingest.ingest_fhfa_hpi(db_session)
    db_session.commit()
    assert count == 2  # the "." value and the unmapped metro are both skipped

    rows = db_session.query(MarketMetric).filter_by(metro_id="testville-ts").all()
    assert {(r.period, r.value) for r in rows} == {(date(2024, 1, 1), 310.5), (date(2024, 7, 1), 315.2)}
    assert all(r.metric == "house_price_index" and r.source == MetricSource.FRED for r in rows)


def test_ingest_fhfa_hpi_missing_file_returns_zero_without_erroring(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(ingest, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ingest, "FHFA_HPI_FILE", "does_not_exist.json")
    assert ingest.ingest_fhfa_hpi(db_session) == 0


# --- _looks_like_a_heading (HUD CHMA chunking, Phase 8) ---
# Real examples pulled directly from actual downloaded reports, not
# invented cases - this heuristic has to work on the real, messy PDF text
# it was built against, not a clean hypothetical.


def test_looks_like_a_heading_accepts_real_section_labels():
    for text in [
        "Rental Market",
        "Economic Conditions",
        "Home Sales Market",
        "Terminology Definitions and Notes",
        "Forecast",
        "Rental Construction Activity Trends",
        "Rental Construction Activity by Type and Geography",
        "Apartment Market Conditions",
    ]:
        assert ingest._looks_like_a_heading(text), text


def test_looks_like_a_heading_accepts_a_label_with_a_trailing_page_number():
    assert ingest._looks_like_a_heading("Rental Market 30")
    assert ingest._looks_like_a_heading("Home Sales Market 24")


def test_looks_like_a_heading_rejects_real_wrapped_prose_lines():
    # Real line-wrapped sentence fragments from an actual report - short
    # and often lacking ending punctuation (cut off mid-sentence by the
    # PDF's line width), which is exactly why "short + no ending
    # punctuation" alone isn't a safe enough signal on its own.
    for text in [
        "slow the spread of the pandemic. This decline",
        "the average second quarter rent for apartments increased",
        "As it has elsewhere in the country,",
        "Jobs grew steadily this year.",
    ]:
        assert not ingest._looks_like_a_heading(text), text


def test_looks_like_a_heading_rejects_long_lines():
    long_sentence = "This Is A Long Title-Cased Line That Goes On For Quite A While And Exceeds The Length Cutoff"
    assert len(long_sentence) > 70
    assert not ingest._looks_like_a_heading(long_sentence)
