-- Same shape as the serving layer's Metro table. Stage 1 doesn't touch
-- census_gross_rent_county (set by the not-yet-migrated rent-trend
-- ingest) - publish_to_sqlite.py never writes to the metros table at
-- all, only market_metrics, so this mart exists for dbt's own tests
-- (e.g. the relationships test on market_metrics.metro_id) rather than
-- being published anywhere itself.

select
    metro_id as id,
    canonical_name,
    state,
    redfin_name,
    aptlist_name,
    census_income_name
from {{ ref('metro_crosswalk') }}
