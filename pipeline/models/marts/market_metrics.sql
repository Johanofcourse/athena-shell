-- Stage 1's slice of the serving layer's market_metrics fact table -
-- only the two sources this pipeline currently owns (redfin, fema).
-- publish_to_sqlite.py reads this mart and replaces exactly the rows in
-- athena.db whose source is in that set - every other source keeps
-- being written by the existing Python ingest, untouched by this table.

select metro_id, period, source, metric, bed_size, value
from {{ ref('stg_redfin__metrics') }}

union all

select
    metro_id,
    -- NRI's own stated release vintage (v1.20, December 2025) - same
    -- constant ingest_market_data.py's FEMA_NRI_PERIOD uses.
    date '2025-12-01' as period,
    'fema' as source,
    'natural_hazard_risk_score' as metric,
    cast(null as varchar) as bed_size,
    natural_hazard_risk_score as value
from {{ ref('int_fema_nri__metro_weighted') }}
