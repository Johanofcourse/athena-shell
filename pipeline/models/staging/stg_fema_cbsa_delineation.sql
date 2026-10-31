-- Thin pass-through over OMB's county-to-CBSA delineation file. Kept as
-- its own staging model (rather than inlined into the intermediate
-- model) so it reads cleanly on its own and the naming-reconstruction
-- logic in int_fema_nri__metro_weighted stays focused on the actual
-- Metro Area / Micro Area join, not raw-column access.

select
    cbsa_code,
    cbsa_title,
    area_type,
    stcofips
from {{ source('raw', 'census_cbsa_delineation') }}
