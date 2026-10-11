"""Fetches median real estate taxes paid, by metro, from Census's ACS
5-Year 2024 Table B25103 ("Mortgage Status by Median Real Estate Taxes
Paid"). Same CBSA geography and metro-name format as the existing
median_household_income and mean_commute_minutes ingests, so it's
matched against metros via the same census_income_name crosswalk field -
no new crosswalk needed. Confirmed by direct comparison against real
API output (e.g. Denver's CBSA named identically in all three: "Denver-
Aurora-Centennial, CO Metro Area"), not assumed.

Census now requires a registered key for every request, not just
high-volume ones (confirmed by testing directly against the API - a
keyless request redirects to missing_key.html). Free, instant signup at
https://api.census.gov/data/key_signup.html - note a freshly-activated
key can take 10-30 seconds to actually start working.

Saves the raw API response to data/samples/ so the actual ingest step
(ingest_census_property_tax in ingest_market_data.py) stays offline and
deterministic, same as every other source in this project.

Run with: python -m app.fetch_census_property_tax
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

from app.config import settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"
OUTPUT_FILE = DATA_DIR / "census_property_tax.json"

CENSUS_API_URL = "https://api.census.gov/data/2024/acs/acs5"
MEDIAN_PROPERTY_TAX_VARIABLE = "B25103_001E"  # Median real estate taxes paid


def fetch() -> None:
    if not settings.census_api_key:
        raise SystemExit("CENSUS_API_KEY is not set in backend/.env")

    params = {
        "get": f"NAME,{MEDIAN_PROPERTY_TAX_VARIABLE}",
        "for": "metropolitan statistical area/micropolitan statistical area:*",
        "key": settings.census_api_key,
    }
    url = f"{CENSUS_API_URL}?{urllib.parse.urlencode(params)}"

    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.loads(response.read())

    if not isinstance(data, list) or len(data) < 2:
        raise SystemExit(f"Unexpected Census API response shape: {data!r}")

    OUTPUT_FILE.write_text(json.dumps(data, indent=2))
    print(f"Saved {len(data) - 1} metro areas to {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch()
