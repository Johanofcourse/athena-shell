-- Population-weighted average of FEMA's county-level risk score, up to
-- one score per metro - the same methodology ingest_fema_nri_risk uses
-- in Python (a real choice, not an arbitrary one: an unweighted average
-- would let a sparsely-populated outlying county pull a metro's score
-- around just as much as its dense urban core). Moved here as SQL so the
-- weighting itself is covered by a dbt test
-- (assert_fema_population_weighting_matches_reference), not just a
-- Python unit test.
--
-- Matches counties to metros via census_income_name, reconstructed into
-- the delineation file's own "<title> Metro/Micro Area" shape - the same
-- join ingest_fema_nri_risk does, since county data only carries a CBSA
-- code, not a metro_id.

with delineation as (
    select
        cbsa_code,
        case
            when area_type = 'Metropolitan Statistical Area' then cbsa_title || ' Metro Area'
            else cbsa_title || ' Micro Area'
        end as census_geography_name,
        stcofips
    from {{ ref('stg_fema_cbsa_delineation') }}
),

crosswalk as (
    select metro_id, census_income_name
    from {{ ref('metro_crosswalk') }}
    -- The seed stores the 10 metro-division gap metros' missing
    -- crosswalk fields as empty strings, not SQL NULL - nullif guards
    -- against either representation.
    where nullif(census_income_name, '') is not null
),

metro_counties as (
    select c.metro_id, d.stcofips
    from crosswalk c
    join delineation d on d.census_geography_name = c.census_income_name
),

county_risk as (
    select stcofips, risk_score, population
    from {{ ref('stg_fema_nri__county_risk') }}
)

select
    mc.metro_id,
    sum(cr.risk_score * cr.population) / sum(cr.population) as natural_hazard_risk_score
from metro_counties mc
join county_risk cr on cr.stcofips = mc.stcofips
group by mc.metro_id
having sum(cr.population) > 0
