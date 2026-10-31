-- Every "Metro"-type region name in Redfin's raw export should resolve
-- to a real metro via the crosswalk seed. A match silently failing here
-- is exactly the class of bug this project has caught before (Apartment
-- List's inconsistent " Metro Area" suffix) - this test catches it the
-- moment Redfin renames or adds a region, instead of it quietly
-- disappearing from market_metrics with no error.

select distinct "REGION NAME" as unmatched_redfin_name
from {{ source('raw', 'redfin_key_metrics') }}
where "REGION TYPE" = 'Metro'
  and "REGION NAME" not in (
      select redfin_name from {{ ref('metro_crosswalk') }}
  )
