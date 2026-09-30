"""Fetches BLS Local Area Unemployment Statistics (unemployment rate) for
the 50 tracked metros via BLS's registered public API - a different,
legitimate access path from the bulk LAUS files this project hit real
bot-gating on earlier (see data/samples/la.area and friends, downloaded
but never usable). Run occasionally, by hand, like the Redfin/Apartment
List "monthly refresh" - not part of the regular offline ingest pipeline,
since this makes a live network call and spends a small amount of the
free key's 500-queries/day quota.

Saves the raw API response to data/samples/ so the actual ingest step
(ingest_bls_unemployment in ingest_market_data.py) stays offline and
deterministic, same as every other source in this project.

Run with: python -m app.fetch_bls_unemployment
"""

import json
import urllib.request
from pathlib import Path

from app.config import settings
from app.market_crosswalk import BLS_AREA_CODES

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"
OUTPUT_FILE = DATA_DIR / "bls_unemployment_rate.json"

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
UNEMPLOYMENT_RATE_MEASURE_CODE = "03"

# A registered key allows up to 20 years per request and 50 series per
# query - 50 series is exactly our metro count, so this is one request,
# not paginated across several.
START_YEAR = "2012"
END_YEAR = "2026"


def fetch() -> None:
    if not settings.bls_api_key:
        raise SystemExit("BLS_API_KEY is not set in backend/.env")

    series_ids = [f"LAU{area_code}{UNEMPLOYMENT_RATE_MEASURE_CODE}" for area_code in BLS_AREA_CODES.values()]
    body = json.dumps(
        {
            "seriesid": series_ids,
            "startyear": START_YEAR,
            "endyear": END_YEAR,
            "registrationkey": settings.bls_api_key,
        }
    ).encode()

    request = urllib.request.Request(
        BLS_API_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read())

    if data.get("status") != "REQUEST_SUCCEEDED":
        raise SystemExit(f"BLS API request failed: {data.get('message')}")

    OUTPUT_FILE.write_text(json.dumps(data, indent=2))
    print(f"Saved {len(data['Results']['series'])} series to {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch()
