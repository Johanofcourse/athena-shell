-- Regression test for a real bug caught during this project's
-- development: the first version of this aggregation used a plain
-- average instead of a population-weighted one, letting a sparsely
-- populated outlying county pull a metro's score around just as much as
-- its dense urban core. For any metro with more than one county and a
-- meaningful population spread between them, the weighted and plain
-- average values should differ - if they're ever equal, the weighting
-- has silently stopped being applied (e.g. someone reverted
-- int_fema_nri__metro_weighted.sql to a plain AVG()).

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
    where nullif(census_income_name, '') is not null
),

metro_counties as (
    select c.metro_id, d.stcofips
    from crosswalk c
    join delineation d on d.census_geography_name = c.census_income_name
),

per_metro as (
    select
        mc.metro_id,
        avg(cr.risk_score) as plain_average_score,
        max(cr.population) - min(cr.population) as population_spread,
        max(cr.risk_score) - min(cr.risk_score) as score_spread,
        count(*) as county_count
    from metro_counties mc
    join {{ ref('stg_fema_nri__county_risk') }} cr on cr.stcofips = mc.stcofips
    group by mc.metro_id
)

select
    p.metro_id,
    p.plain_average_score,
    w.natural_hazard_risk_score as weighted_score
from per_metro p
join {{ ref('int_fema_nri__metro_weighted') }} w on w.metro_id = p.metro_id
-- Only a real failure signal for a metro where weighting could actually
-- change the answer: multiple counties, a meaningful population skew
-- between them, AND a meaningful difference in their raw risk scores -
-- confirmed against real data that a metro can have a large population
-- skew (e.g. Riverside-CA, a ~237k spread) but near-identical risk
-- scores across its counties, where weighted and plain averages land
-- within 0.01 of each other for a completely legitimate reason. Without
-- the score_spread guard this test flagged that metro as a false
-- positive.
where p.county_count > 1
  and p.population_spread > 1000
  and p.score_spread > 1.0
  and abs(p.plain_average_score - w.natural_hazard_risk_score) < 0.01
