"""Fetches FEMA's National Risk Index (NRI) county-level composite risk
score - a free, government source covering 18 natural hazards (flood,
wildfire, hurricane, earthquake, and others), combined into one 0-100
national percentile score per county. Genuinely different from
everything else this project tracks: it's the only metric here that
isn't about market activity or demographics, and it's the only one with
no live API at all - FEMA's own OpenFEMA listing for this dataset says
"OpenFEMA API: N/A. Files Only." (confirmed directly against their
data-sets page), so this is a plain bulk-file download, not a
registered-key API call like the other recent additions.

Downloads the Table Format county data (a zip containing a ~25MB CSV,
a data dictionary, and metadata), extracts just the 5 columns actually
needed (STCOFIPS, COUNTY, STATEABBRV, RISK_SCORE, POPULATION) out of
its real 465, and saves that trimmed CSV to data/samples/ - no reason
to commit 460 unused columns (building value, every individual hazard's
own frequency/severity/loss breakdown, social vulnerability, community
resilience, etc.) when ingest_fema_nri_risk only ever needs these five.

RISK_SCORE is NRI's own flagship composite ("National Risk Index -
Score - Composite" per its data dictionary) - worth knowing it reflects
EXPOSURE-weighted risk (population and building value at stake,
combined with hazard frequency/severity), not hazard probability alone,
so a large, valuable metro can score "high risk" even with only
moderate hazard likelihood simply because more is at stake there. This
is FEMA's own headline number, not a cherry-picked alternative.

County-to-metro aggregation (population-weighted average across a
CBSA's constituent counties, via data/samples/
census_cbsa_county_delineation.csv) happens in ingest_fema_nri_risk,
not here - this script only fetches and trims, consistent with the
fetch/ingest split everywhere else in this project.

Run with: python -m app.fetch_fema_nri
"""

import csv
import io
import subprocess
import tempfile
import zipfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"
OUTPUT_FILE = DATA_DIR / "fema_nri_county_risk.csv"

NRI_COUNTIES_ZIP_URL = "https://www.fema.gov/about/reports-and-data/openfema/nri/v120/NRI_Table_Counties.zip"
SOURCE_CSV_NAME = "NRI_Table_Counties.csv"
KEPT_COLUMNS = ["STCOFIPS", "COUNTY", "STATEABBRV", "RISK_SCORE", "POPULATION"]


def fetch() -> None:
    # Shells out to curl rather than urllib, deliberately - confirmed by
    # testing that FEMA's CDN (Akamai) blocks this specific download with
    # a 403 for every urllib request regardless of headers (even an empty
    # User-Agent, even a realistic browser one), while curl succeeds
    # unconditionally. That's consistent with TLS/HTTP-stack
    # fingerprinting (curl and urllib negotiate differently at the
    # handshake level), not anything fixable by setting a header from
    # Python - curl is the one tool confirmed to actually get through.
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "nri.zip"
        subprocess.run(
            ["curl", "-sf", "-o", str(zip_path), NRI_COUNTIES_ZIP_URL],
            check=True,
            timeout=60,
        )
        with zipfile.ZipFile(zip_path) as zf, zf.open(SOURCE_CSV_NAME) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            rows = [{col: row[col] for col in KEPT_COLUMNS} for row in reader]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=KEPT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} counties to {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch()
