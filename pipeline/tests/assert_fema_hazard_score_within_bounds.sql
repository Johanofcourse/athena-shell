-- FEMA's National Risk Index composite score is documented on a 0-100
-- scale. A population-weighted average of in-bounds county scores
-- should always land back inside that range - if it doesn't, something
-- in the join or the weighting math is wrong (e.g. a county matched to
-- the wrong metro, or a population figure in the wrong units).

select metro_id, natural_hazard_risk_score
from {{ ref('int_fema_nri__metro_weighted') }}
where natural_hazard_risk_score < 0 or natural_hazard_risk_score > 100
