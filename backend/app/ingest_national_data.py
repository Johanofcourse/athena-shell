"""Loads Freddie Mac's Primary Mortgage Market Survey (PMMS) - the first
national, non-metro-specific series in this app - into NationalMetric.
Kept separate from ingest_market_data.py on purpose: this doesn't go
through the metro crosswalk at all, since there's no metro dimension to
join against.

Not run standalone - called from ingest_market_data.ingest() so a fresh
setup is still one command. See NationalMetric's docstring for why this
isn't just another Metro row.
"""

import csv
from datetime import datetime
from pathlib import Path

from app.models import MetricSource, NationalMetric

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"

PMMS_FILE = "freddiemac_pmms_history.csv"

# Only the three headline rate series - not Freddie Mac's points/margin/
# spread columns, which are more esoteric mortgage-industry detail than
# anything a user is likely to ask this app about (same reasoning as
# skipping Redfin's precomputed YOY columns elsewhere in this project).
PMMS_SERIES = {
    "pmms30": "mortgage_rate_30yr_fixed",
    "pmms15": "mortgage_rate_15yr_fixed",
    "pmms51": "mortgage_rate_5_1_arm",
}


def _parse_float(raw: str | None) -> float | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def ingest_pmms(db) -> int:
    count = 0
    with open(DATA_DIR / PMMS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            period = datetime.strptime(row["date"], "%m/%d/%Y").date()
            for column, metric_name in PMMS_SERIES.items():
                value = _parse_float(row.get(column))
                if value is None:
                    continue
                db.add(
                    NationalMetric(
                        period=period,
                        source=MetricSource.FREDDIE_MAC,
                        metric=metric_name,
                        value=value,
                    )
                )
                count += 1
    return count
