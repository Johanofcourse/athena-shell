-- Reshapes Redfin's three wide monthly exports (price drops, delistings/
-- relistings, key metrics) into the long (metro_id, period, metric, value)
-- shape the serving layer's market_metrics table uses - the same column
-- mapping backend/app/ingest_market_data.py's REDFIN_FILES constant
-- encodes in Python, moved here as SQL so it runs through dbt's test
-- suite instead of only unit tests.

with price_drops as (
    select *
    from {{ source('raw', 'redfin_price_drops') }}
    where "REGION TYPE" = 'Metro'
),

delistings as (
    select *
    from {{ source('raw', 'redfin_delistings_relistings') }}
    where "REGION TYPE" = 'Metro'
),

key_metrics as (
    select *
    from {{ source('raw', 'redfin_key_metrics') }}
    where "REGION TYPE" = 'Metro'
),

crosswalk as (
    select metro_id, redfin_name
    from {{ ref('metro_crosswalk') }}
),

unioned as (
    select "REGION NAME" as redfin_name, "PERIOD BEGIN"::date as period,
        'price_drop_count' as metric, try_cast("PRICE DROPS" as double) as value
    from price_drops
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'price_drop_pct_avg', try_cast("AVERAGE SIZE OF PRICE DROP (%)" as double)
    from price_drops
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'pct_active_with_price_drop', try_cast("PERCENT ACTIVE WITH PRICE DROPS (%)" as double)
    from price_drops
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'homes_sold_with_price_drop', try_cast("HOMES SOLD WITH PRICE DROPS" as double)
    from price_drops
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'total_delistings', try_cast("TOTAL DELISTINGS" as double)
    from delistings
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'total_relistings', try_cast("TOTAL RELISTINGS" as double)
    from delistings
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'share_delisted_pct', try_cast("SHARE OF LISTINGS DELISTED (%)" as double)
    from delistings
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'share_relisted_pct', try_cast("SHARE OF LISTINGS RELISTED (%)" as double)
    from delistings
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'homes_sold', try_cast("HOMES SOLD" as double)
    from key_metrics
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'median_sale_price', try_cast("MEDIAN SALE PRICE NSA ($)" as double)
    from key_metrics
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'median_days_on_market', try_cast("MEDIAN DAYS ON MARKET (DAYS)" as double)
    from key_metrics
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'new_listings', try_cast("NEW LISTINGS" as double)
    from key_metrics
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'active_listings', try_cast("ACTIVE LISTINGS" as double)
    from key_metrics
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'pending_sales', try_cast("PENDING SALES" as double)
    from key_metrics
    union all
    select "REGION NAME", "PERIOD BEGIN"::date,
        'median_price_per_sqft', try_cast("MEDIAN NEW LISTING PRICE PER SQ.FT. ($)" as double)
    from key_metrics
)

select
    c.metro_id,
    u.period,
    'redfin' as source,
    u.metric,
    cast(null as varchar) as bed_size,
    u.value
from unioned u
join crosswalk c on c.redfin_name = u.redfin_name
where u.value is not null
