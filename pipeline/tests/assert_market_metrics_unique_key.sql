-- The serving layer enforces this as a real UniqueConstraint
-- (metro_id, period, source, metric, bed_size) - see backend/app/models.py
-- MarketMetric. SQLite will reject a genuine duplicate at publish time,
-- but failing here, inside the pipeline, points straight at the model
-- that produced it instead of a cryptic IntegrityError three steps later.

select metro_id, period, source, metric, bed_size, count(*) as row_count
from {{ ref('market_metrics') }}
group by 1, 2, 3, 4, 5
having count(*) > 1
