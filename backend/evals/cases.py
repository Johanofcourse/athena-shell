"""18 representative queries against the real market-metrics NL layer.
Each case checks only the fields that actually matter for it - not full
equality against one hardcoded filter object, since the model has
legitimate freedom in exactly which metros list or period range it picks.

Chosen to cover, deliberately: every metric category, both query modes
(trend vs. ranking), bed_size and time-range parsing, and - the point of
this whole redesign - all three honesty behaviors: unsupported_aspects,
no_data_metros, and unmatched_metros. These aren't edge cases bolted on
after the fact; they're the reason this eval exists.
"""

CASES = [
    {
        "id": "sale_price_single_metro",
        "query": "What's the median sale price in Denver?",
        "expect_metric": ["median_sale_price"],
        "expect_metros_contains": ["denver"],
        "expect_sort_by": "period",
    },
    {
        "id": "rent_single_metro",
        "query": "How much is rent in Seattle?",
        "expect_metric": ["median_rent"],
        "expect_metros_contains": ["seattle"],
        "expect_sort_by": "period",
    },
    {
        "id": "days_on_market",
        "query": "How long are homes sitting on the market in Phoenix?",
        "expect_metric": ["median_days_on_market"],
        "expect_metros_contains": ["phoenix"],
    },
    {
        "id": "vacancy_rate",
        "query": "What's the vacancy rate in Chicago?",
        "expect_metric": ["vacancy_rate"],
        "expect_metros_contains": ["chicago"],
    },
    {
        "id": "rental_time_on_market",
        "query": "How fast do rentals lease up in Boston?",
        "expect_metric": ["time_on_market_days"],
        "expect_metros_contains": ["boston"],
    },
    {
        "id": "price_drop_trend",
        "query": "Show me price drop trends in Miami",
        # Genuinely ambiguous which price-drop metric best fits "trends" -
        # any of these three is a defensible answer, per the metric-choice
        # non-determinism we actually observed testing this by hand.
        "expect_metric": ["price_drop_pct_avg", "price_drop_count", "pct_active_with_price_drop"],
        "expect_metros_contains": ["miami"],
        "expect_sort_by": "period",
    },
    {
        "id": "relisting_rate",
        "query": "How often are homes relisted in Tampa?",
        "expect_metric": ["total_relistings", "share_relisted_pct"],
        "expect_metros_contains": ["tampa"],
    },
    {
        "id": "ranking_price_drops",
        "query": "Which metros have the biggest price drops right now?",
        "expect_metric": ["price_drop_pct_avg", "price_drop_count", "pct_active_with_price_drop"],
        "expect_metros_empty": True,
        "expect_sort_by": "value",
    },
    {
        "id": "ranking_highest_rent",
        "query": "Which metro has the highest rent?",
        "expect_metric": ["median_rent"],
        "expect_metros_empty": True,
        "expect_sort_by": "value",
        "expect_sort_order": "desc",
    },
    {
        "id": "ranking_cheapest",
        "query": "Where are home prices lowest right now?",
        "expect_metric": ["median_sale_price"],
        "expect_metros_empty": True,
        "expect_sort_by": "value",
        "expect_sort_order": "asc",
    },
    {
        "id": "multi_metro_compare",
        "query": "Compare Austin and Denver home prices",
        "expect_metric": ["median_sale_price"],
        "expect_metros_contains": ["austin", "denver"],
        "expect_sort_by": "period",
    },
    {
        "id": "bed_size_specific",
        "query": "What's the average rent for a 2 bedroom in San Diego?",
        "expect_metric": ["median_rent"],
        "expect_metros_contains": ["san diego"],
        "expect_bed_size": "2br",
    },
    {
        "id": "time_range_specific",
        "query": "How has Seattle rent changed since 2020?",
        "expect_metric": ["median_rent"],
        "expect_metros_contains": ["seattle"],
        "expect_start_period_prefix": "2020",
    },
    {
        "id": "unsupported_schools",
        "query": "Is Austin near good schools?",
        "expect_unsupported_nonempty": True,
    },
    {
        "id": "unsupported_crime",
        "query": "What's the crime rate in Chicago?",
        "expect_unsupported_nonempty": True,
    },
    {
        "id": "unsupported_specific_address",
        "query": "What's the value of 123 Main St in Austin?",
        "expect_unsupported_nonempty": True,
    },
    {
        "id": "no_data_metro",
        "query": "What's the rent trend in Anaheim?",
        "expect_metros_contains": ["anaheim"],
        "expect_no_data_nonempty": True,
    },
    {
        "id": "unmatched_metro",
        "query": "What are home prices like in Atlantis?",
        "expect_unmatched_nonempty": True,
    },
]
