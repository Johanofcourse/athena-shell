"""Fetches median gross rent (Census ACS 1-Year Table B25064), by county,
for each year Census has published one for (2012-2024, skipping 2020 -
same COVID-19 field-work gap as fetch_census_population.py), for the 10
counties behind the metro-division gap metros (Anaheim, Fort Lauderdale,
Fort Worth, Montgomery County PA, Nassau County NY, New Brunswick,
Newark, Oakland, Warren, West Palm Beach - see ingest_census_rent_trend
in ingest_market_data.py for how this gets turned into MarketMetric
rows).

Replaces what was a single ACS 5-Year 2024 snapshot per metro (one point,
no trend) with a real multi-year 1-Year series - confirmed directly
against the API before building this that 1-Year estimates actually
exist back to 2012 for all 10 counties (every one is well past the
65,000-population threshold 1-Year estimates require). Deliberately
1-Year, not 5-Year, for the same reason fetch_census_population.py is:
overlapping 5-Year windows don't give a clean year-over-year change the
way independent 1-Year estimates do.

County geography, not CBSA - these specific places aren't their own
CBSA/metro-division entries in the ACS 1-Year table at all (that's the
whole reason they're gap metros), but metro divisions are officially
defined as whole counties, so county-level B25064 gives a real,
non-blended number for exactly these 10.

Census now requires a registered key for every request. Saves one
combined JSON file (year -> raw API rows) to data/samples/ so the actual
ingest step (ingest_census_rent_trend in ingest_market_data.py) stays
offline and deterministic, same as every other source here.

Run with: python -m app.fetch_census_rent_trend
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

from app.config import settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"
OUTPUT_FILE = DATA_DIR / "census_rent_trend.json"

CENSUS_API_URL_TEMPLATE = "https://api.census.gov/data/{year}/acs/acs1"
MEDIAN_GROSS_RENT_VARIABLE = "B25064_001E"

# (state FIPS, county FIPS, metro_id) - confirmed directly against the
# API (NAME in the response matches the expected county) before being
# hardcoded here, not assumed from memory.
COUNTIES: list[tuple[str, str, str]] = [
    ("06", "001", "oakland-ca"),  # Alameda County, CA
    ("06", "059", "anaheim-ca"),  # Orange County, CA
    ("48", "439", "fort-worth-tx"),  # Tarrant County, TX
    ("42", "091", "montgomery-county-pa"),  # Montgomery County, PA
    ("36", "059", "nassau-county-ny"),  # Nassau County, NY
    ("26", "099", "warren-mi"),  # Macomb County, MI
    ("12", "011", "fort-lauderdale-fl"),  # Broward County, FL
    ("12", "099", "west-palm-beach-fl"),  # Palm Beach County, FL
    ("34", "013", "newark-nj"),  # Essex County, NJ
    ("34", "023", "new-brunswick-nj"),  # Middlesex County, NJ
]

# 2020 excluded deliberately - see module docstring.
YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]


def fetch() -> None:
    if not settings.census_api_key:
        raise SystemExit("CENSUS_API_KEY is not set in backend/.env")

    result: dict[str, dict[str, dict[str, str]]] = {}
    for year in YEARS:
        year_rows: dict[str, dict[str, str]] = {}
        for state_fips, county_fips, metro_id in COUNTIES:
            params = {
                "get": f"NAME,{MEDIAN_GROSS_RENT_VARIABLE}",
                "for": f"county:{county_fips}",
                "in": f"state:{state_fips}",
                "key": settings.census_api_key,
            }
            url = f"{CENSUS_API_URL_TEMPLATE.format(year=year)}?{urllib.parse.urlencode(params)}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read())
            if not isinstance(data, list) or len(data) != 2:
                raise SystemExit(f"Unexpected Census API response for {year}/{metro_id}: {data!r}")
            header, row = data
            year_rows[metro_id] = dict(zip(header, row))
        result[str(year)] = year_rows
        print(f"{year}: {len(year_rows)} counties")

    OUTPUT_FILE.write_text(json.dumps(result, indent=2))
    print(f"Saved {len(result)} years to {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch()
