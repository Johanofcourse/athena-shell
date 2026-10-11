"""Fetches total population, by metro, for each ACS 1-Year survey year
Census has published one for (2012-2024, skipping 2020 - the one year
ACS 1-Year wasn't fielded normally because of COVID-19 field-work
disruptions, a real, documented gap, not a bug here). Source: ACS
1-Year Table B01003 ("Total Population"). Deliberately 1-Year, not
5-Year: 5-Year estimates are heavily overlapping rolling windows (each
one blends 5 years of collection), which makes a year-over-year
difference between two 5-Year estimates mostly re-measuring the same
overlapping data, not a clean annual change - 1-Year estimates don't
have that problem, at the cost of only covering geographies with
65,000+ population (every metro this project tracks clears that
easily).

Deliberately NOT the Population Estimates Program (PEP), despite that
being the more obvious-sounding source: confirmed by testing directly
against the API that PEP's own metro-area geography support is
inconsistent across vintages (present in the 2019 vintage, silently
dropped from 2021's, and no vintage newer than 2021 exists for this
dataset under its current name at all) - not something to build a
"real data" feature on.

Same CBSA geography and metro-name format as median_household_income,
mean_commute_minutes, and median_property_tax - confirmed by direct
comparison, not assumed - so it reuses that same census_income_name
crosswalk.

Census now requires a registered key for every request. Saves one
combined JSON file (year -> raw API rows) to data/samples/ so the
actual ingest step (ingest_census_population in ingest_market_data.py)
stays offline and deterministic, same as every other source here.

Run with: python -m app.fetch_census_population
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

from app.config import settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"
OUTPUT_FILE = DATA_DIR / "census_population.json"

CENSUS_API_URL_TEMPLATE = "https://api.census.gov/data/{year}/acs/acs1"
TOTAL_POPULATION_VARIABLE = "B01003_001E"

# 2020 excluded deliberately - see module docstring.
YEARS = [2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]


def fetch() -> None:
    if not settings.census_api_key:
        raise SystemExit("CENSUS_API_KEY is not set in backend/.env")

    result: dict[str, list] = {}
    for year in YEARS:
        params = {
            "get": f"NAME,{TOTAL_POPULATION_VARIABLE}",
            "for": "metropolitan statistical area/micropolitan statistical area:*",
            "key": settings.census_api_key,
        }
        url = f"{CENSUS_API_URL_TEMPLATE.format(year=year)}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read())
        if not isinstance(data, list) or len(data) < 2:
            raise SystemExit(f"Unexpected Census API response shape for {year}: {data!r}")
        result[str(year)] = data
        print(f"{year}: {len(data) - 1} metro areas")

    OUTPUT_FILE.write_text(json.dumps(result, indent=2))
    print(f"Saved {len(result)} years to {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch()
