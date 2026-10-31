-- Thin rename/cast pass over FEMA's raw county-level National Risk Index
-- export. Rows with an unparseable score or population are dropped here
-- (mirrors ingest_fema_nri_risk's "if risk is not None and pop is not
-- None" guard) rather than silently propagating a null into the
-- weighted-average math downstream.

select
    "STCOFIPS" as stcofips,
    try_cast("RISK_SCORE" as double) as risk_score,
    try_cast("POPULATION" as double) as population
from {{ source('raw', 'fema_nri_county_risk') }}
where try_cast("RISK_SCORE" as double) is not null
  and try_cast("POPULATION" as double) is not null
