"""Fetches FHFA's All-Transactions House Price Index by metro, via FRED
(Federal Reserve Economic Data)'s registered public API - a genuinely
independent, differently-computed home-price benchmark alongside
Redfin's own median sale price (a repeat-sales index vs. a median
transaction price), always kept as its own metric, never blended with
Redfin's numbers.

Unlike BLS's batch endpoint, FRED's series/observations endpoint takes
one series at a time - 38 sequential requests (well within FRED's
generous per-minute limit), not paginated across days.

Saves the raw responses to data/samples/ so the actual ingest step
(ingest_fhfa_hpi in ingest_market_data.py) stays offline and
deterministic, same as every other source in this project. Run
occasionally, by hand, like the other refreshes - not part of the
regular ingest pipeline.

Run with: python -m app.fetch_fred_house_price_index
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

from app.config import settings
from app.market_crosswalk import FHFA_HPI_SERIES_IDS

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"
OUTPUT_FILE = DATA_DIR / "fred_house_price_index.json"

FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"

# Matches the other sources' Jan 2012 start where possible - FHFA's data
# actually goes back to 1995, but there's no reason to carry decades of
# history nothing else in this app spans.
OBSERVATION_START = "2012-01-01"


def fetch() -> None:
    if not settings.fred_api_key:
        raise SystemExit("FRED_API_KEY is not set in backend/.env")

    results = {}
    for metro_id, series_id in FHFA_HPI_SERIES_IDS.items():
        params = urllib.parse.urlencode(
            {
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "observation_start": OBSERVATION_START,
            }
        )
        with urllib.request.urlopen(f"{FRED_OBSERVATIONS_URL}?{params}", timeout=20) as response:
            data = json.loads(response.read())
        results[metro_id] = {"series_id": series_id, "observations": data["observations"]}
        print(f"  {metro_id}: {len(data['observations'])} observations")

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print(f"Saved {len(results)} series to {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch()
