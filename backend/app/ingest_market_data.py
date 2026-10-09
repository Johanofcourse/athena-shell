"""Loads the real Redfin + Apartment List market data (see
docs/ROADMAP.md Phase 3) into the Metro/MarketMetric tables.

Run with: python -m app.ingest_market_data
"""

import csv
import json
import re
from datetime import date
from pathlib import Path

import pypdf

from app.database import Base, SessionLocal, engine
from app.ingest_national_data import ingest_pmms
from app.market_crosswalk import BLS_AREA_CODES, FHFA_HPI_SERIES_IDS, HUD_CHMA_FILES, METRO_CROSSWALK
from app.models import MarketCommentaryChunk, MarketMetric, MetricSource, Metro

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "samples"

# Only the direct measured columns - not the precomputed YOY columns.
# Trend/comparison math is the query layer's job, computed on demand from
# these raw values, not baked in twice (same reasoning we used to skip
# Apartment List's separate Rent Growth files).
REDFIN_FILES = [
    (
        "redfin_price_drops_monthly_top_50_metros_2012_Jan_to_2026_Aug.csv",
        {
            "PRICE DROPS": "price_drop_count",
            "AVERAGE SIZE OF PRICE DROP (%)": "price_drop_pct_avg",
            "PERCENT ACTIVE WITH PRICE DROPS (%)": "pct_active_with_price_drop",
            "HOMES SOLD WITH PRICE DROPS": "homes_sold_with_price_drop",
        },
    ),
    (
        "redfin_delistings_relistings_monthly_top_50_metros_2012_Jan_to_2026_Aug.csv",
        {
            "TOTAL DELISTINGS": "total_delistings",
            "TOTAL RELISTINGS": "total_relistings",
            "SHARE OF LISTINGS DELISTED (%)": "share_delisted_pct",
            "SHARE OF LISTINGS RELISTED (%)": "share_relisted_pct",
        },
    ),
    (
        "redfin_housing_market_monthly_top_50_metros_key_metrics_2012_Jan_to_2026_Aug.csv",
        {
            "HOMES SOLD": "homes_sold",
            "MEDIAN SALE PRICE NSA ($)": "median_sale_price",
            "MEDIAN DAYS ON MARKET (DAYS)": "median_days_on_market",
            "NEW LISTINGS": "new_listings",
            "ACTIVE LISTINGS": "active_listings",
            "PENDING SALES": "pending_sales",
            "MEDIAN NEW LISTING PRICE PER SQ.FT. ($)": "median_price_per_sqft",
        },
    ),
]

APARTMENT_LIST_FILES = [
    ("apartmentlist_rent_estimates_2017_to_2026_08.csv", "median_rent", True),
    ("apartmentlist_vacancy_index_2017_to_2026_08.csv", "vacancy_rate", False),
    ("apartmentlist_time_on_market_2019_to_2026_08.csv", "time_on_market_days", False),
]

CENSUS_INCOME_FILE = "ACSDT5Y2024.B19013-2026-09-28T020212.csv"

# The 10 metro-division metros (Anaheim, Fort Lauderdale, Fort Worth,
# Montgomery County PA, Nassau County NY, New Brunswick NJ, Newark NJ,
# Oakland, Warren, West Palm Beach) have no aptlist_name and no
# census_income_name - Apartment List and Census's metro-level income
# table both only publish the larger combined metro. Metro divisions are
# officially defined as whole counties, though, so county-level Census
# gross rent (a different table, B25064) gives a real, non-blended number
# for exactly these 10 - ingested as its own metric (median_gross_rent),
# never silently relabeled as median_rent. See run_market_query for how
# it's surfaced (always as an explicitly flagged approximation).
CENSUS_GROSS_RENT_GAP_FILES: list[tuple[str, dict[str, str]]] = [
    (
        "ACSDT5Y2024.B25064-2026-09-28T041101.csv",
        {"Alameda County, California": "oakland-ca", "Orange County, California": "anaheim-ca"},
    ),
    ("ACSDT5Y2024.B25064-2026-09-28T041221.csv", {"Tarrant County, Texas": "fort-worth-tx"}),
    ("ACSDT5Y2024.B25064-2026-09-28T041311.csv", {"Montgomery County, Pennsylvania": "montgomery-county-pa"}),
    ("ACSDT5Y2024.B25064-2026-09-28T041414.csv", {"Nassau County, New York": "nassau-county-ny"}),
    ("ACSDT5Y2024.B25064-2026-09-28T041458.csv", {"Macomb County, Michigan": "warren-mi"}),
    (
        "ACSDT5Y2024.B25064-2026-09-28T041653.csv",
        {"Broward County, Florida": "fort-lauderdale-fl", "Palm Beach County, Florida": "west-palm-beach-fl"},
    ),
    (
        "ACSDT5Y2024.B25064-2026-09-28T041749.csv",
        {"Essex County, New Jersey": "newark-nj", "Middlesex County, New Jersey": "new-brunswick-nj"},
    ),
]

# Both Census tables are single-snapshot ACS 5-Year 2024 estimates, not a
# monthly series like Redfin/Apartment List - stored under one
# representative period so they still fit the shared
# (metro, period, source, metric) fact table.
CENSUS_ACS_PERIOD = date(2024, 1, 1)


def _normalize_aptlist_name(name: str) -> str:
    """Apartment List isn't consistent with its own naming across files -
    Time on Market suffixes every name with " Metro Area", Rent Estimates
    and Vacancy Index don't. Confirmed by testing: an exact-string lookup
    silently matched zero rows in the Time on Market file until this
    normalization was added."""
    suffix = " Metro Area"
    return name[: -len(suffix)] if name.endswith(suffix) else name


def _parse_float(raw: str) -> float | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def load_metros(db) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Returns {redfin_name: metro_id}, {aptlist_name: metro_id}, and
    {census_income_name: metro_id} for the ingest loops below."""
    redfin_to_id = {}
    aptlist_to_id = {}
    income_to_id = {}
    for metro_id, canonical_name, state, redfin_name, aptlist_name, census_income_name in METRO_CROSSWALK:
        if db.get(Metro, metro_id) is None:
            db.add(
                Metro(
                    id=metro_id,
                    canonical_name=canonical_name,
                    state=state,
                    redfin_name=redfin_name,
                    aptlist_name=aptlist_name,
                    census_income_name=census_income_name,
                )
            )
        redfin_to_id[redfin_name] = metro_id
        if aptlist_name:
            aptlist_to_id[aptlist_name] = metro_id
        if census_income_name:
            income_to_id[census_income_name] = metro_id
    db.commit()
    return redfin_to_id, aptlist_to_id, income_to_id


def ingest_redfin(db, redfin_to_id: dict[str, str]) -> int:
    count = 0
    for filename, column_map in REDFIN_FILES:
        path = DATA_DIR / filename
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["REGION TYPE"] != "Metro":
                    continue
                metro_id = redfin_to_id.get(row["REGION NAME"])
                if metro_id is None:
                    continue
                period = date.fromisoformat(row["PERIOD BEGIN"])
                for column, metric_name in column_map.items():
                    value = _parse_float(row.get(column))
                    if value is None:
                        continue
                    db.add(
                        MarketMetric(
                            metro_id=metro_id,
                            period=period,
                            source=MetricSource.REDFIN,
                            metric=metric_name,
                            bed_size=None,
                            value=value,
                        )
                    )
                    count += 1
    return count


def ingest_apartment_list(db, aptlist_to_id: dict[str, str]) -> int:
    count = 0
    for filename, metric_name, split_by_bed_size in APARTMENT_LIST_FILES:
        path = DATA_DIR / filename
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            month_columns = [c for c in reader.fieldnames if c and c[:4].isdigit() and c[4] == "_"]
            for row in reader:
                if row["location_type"] != "Metro":
                    continue
                metro_id = aptlist_to_id.get(_normalize_aptlist_name(row["location_name"]))
                if metro_id is None:
                    continue
                bed_size = row.get("bed_size") if split_by_bed_size else None
                for col in month_columns:
                    value = _parse_float(row.get(col))
                    if value is None:
                        continue
                    year, month = col.split("_")
                    period = date(int(year), int(month), 1)
                    db.add(
                        MarketMetric(
                            metro_id=metro_id,
                            period=period,
                            source=MetricSource.APARTMENT_LIST,
                            metric=metric_name,
                            bed_size=bed_size,
                            value=value,
                        )
                    )
                    count += 1
    return count


def _parse_census_row(path: Path) -> dict[str, float]:
    """Census's 'Compare' CSV export: one label row, then one data row with
    Estimate/Margin-of-error columns interleaved per geography. Returns
    {geography_name: estimate_value}, dropping the margin-of-error columns
    and comma thousands separators."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header, data = rows[0], rows[1]
    values = {}
    for i in range(1, len(header), 2):
        geography = header[i].split("!!")[0]
        value = _parse_float(data[i].replace(",", ""))
        if value is not None:
            values[geography] = value
    return values


def ingest_census_income(db, income_to_id: dict[str, str]) -> int:
    values = _parse_census_row(DATA_DIR / CENSUS_INCOME_FILE)
    count = 0
    for geography, metro_id in income_to_id.items():
        value = values.get(geography)
        if value is None:
            continue
        db.add(
            MarketMetric(
                metro_id=metro_id,
                period=CENSUS_ACS_PERIOD,
                source=MetricSource.CENSUS,
                metric="median_household_income",
                bed_size=None,
                value=value,
            )
        )
        count += 1
    return count


def ingest_census_gross_rent_fallback(db) -> int:
    count = 0
    for filename, county_to_metro in CENSUS_GROSS_RENT_GAP_FILES:
        values = _parse_census_row(DATA_DIR / filename)
        for county_name, metro_id in county_to_metro.items():
            value = values.get(county_name)
            if value is None:
                continue
            db.add(
                MarketMetric(
                    metro_id=metro_id,
                    period=CENSUS_ACS_PERIOD,
                    source=MetricSource.CENSUS,
                    metric="median_gross_rent",
                    bed_size=None,
                    value=value,
                )
            )
            # Recorded on the metro itself (not just derivable from this
            # function's file list) so the caveat shown to a user can name
            # the specific county behind the number - "Orange County, CA",
            # not just a generic "Census data" gesture.
            db.get(Metro, metro_id).census_gross_rent_county = county_name
            count += 1
    return count


BLS_UNEMPLOYMENT_FILE = "bls_unemployment_rate.json"


def ingest_bls_unemployment(db) -> int:
    """Parses the raw response saved by fetch_bls_unemployment.py (a live,
    registered BLS API call, not a bulk file download) into MarketMetric
    rows. Optional: skips cleanly with a message if that file hasn't been
    fetched yet, rather than failing the whole ingest run - this is the
    newest source and the least likely to already be present on a fresh
    checkout."""
    path = DATA_DIR / BLS_UNEMPLOYMENT_FILE
    if not path.exists():
        print(f"{BLS_UNEMPLOYMENT_FILE} not found - run `python -m app.fetch_bls_unemployment` first. Skipping.")
        return 0

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    area_code_to_metro_id = {area_code: metro_id for metro_id, area_code in BLS_AREA_CODES.items()}
    count = 0
    for series in payload["Results"]["series"]:
        # series_id = "LAU" + area_code (15 chars) + 2-digit measure code.
        area_code = series["seriesID"][3:-2]
        metro_id = area_code_to_metro_id.get(area_code)
        if metro_id is None:
            continue
        for point in series["data"]:
            value = _parse_float(point.get("value"))
            if value is None:
                continue
            period = date(int(point["year"]), int(point["period"][1:]), 1)
            db.add(
                MarketMetric(
                    metro_id=metro_id,
                    period=period,
                    source=MetricSource.BLS,
                    metric="unemployment_rate",
                    bed_size=None,
                    value=value,
                )
            )
            count += 1
    return count


FHFA_HPI_FILE = "fred_house_price_index.json"


def ingest_fhfa_hpi(db) -> int:
    """Parses the raw responses saved by fetch_fred_house_price_index.py
    (38 live FRED API calls, not a bulk download) into MarketMetric rows.
    Optional, like ingest_bls_unemployment - skips cleanly if the file
    hasn't been fetched yet rather than failing the whole ingest run."""
    path = DATA_DIR / FHFA_HPI_FILE
    if not path.exists():
        print(f"{FHFA_HPI_FILE} not found - run `python -m app.fetch_fred_house_price_index` first. Skipping.")
        return 0

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    count = 0
    for metro_id, series in payload.items():
        if metro_id not in FHFA_HPI_SERIES_IDS:
            continue
        for point in series["observations"]:
            value = _parse_float(point.get("value"))
            if value is None:
                continue
            year, month, _ = point["date"].split("-")
            period = date(int(year), int(month), 1)
            db.add(
                MarketMetric(
                    metro_id=metro_id,
                    period=period,
                    source=MetricSource.FRED,
                    metric="house_price_index",
                    bed_size=None,
                    value=value,
                )
            )
            count += 1
    return count


HUD_CHMA_DIR = DATA_DIR / "hud_chma"

# These repeated header/footer lines appear on every page of a CHMA PDF
# (confirmed across multiple metros and both the current template and the
# older one LA's 2013 report uses, where PDF kerning breaks some words
# apart - e.g. "ANAL YSIS" - so matching on the shorter, unbroken
# "comprehensive housing market" substring catches both). Filtering them
# out keeps the real section label (the page's actual first remaining
# line) and the real content from getting diluted with boilerplate that
# would otherwise dominate a small per-metro chunk set during ranking.
_CHMA_BOILERPLATE_MARKERS = (
    "comprehensive housing market",
    "u.s. department of housing and urban development",
    "office of policy development and research",
)
_CHMA_DATE_RE = re.compile(r"[Aa]s [Oo]f\s+([A-Z][a-z]+ \d{1,2},?\s*\d{4})")


def ingest_hud_chma(db) -> int:
    """Extracts and chunks the hand-downloaded HUD CHMA PDFs (see
    HUD_CHMA_FILES for which metros, and why only those) into
    MarketCommentaryChunk rows, one per PDF page - these reports are
    already organized into named sections that map one-to-one onto pages,
    so page-level chunking preserves real structure rather than cutting
    mid-thought. Skips a metro cleanly, like ingest_bls_unemployment, if
    its PDF hasn't been downloaded yet - this corpus is deliberately
    partial and grows over time, not a hard ingest failure."""
    count = 0
    for metro_id, filename in HUD_CHMA_FILES.items():
        path = HUD_CHMA_DIR / filename
        if not path.exists():
            print(f"{filename} not found for {metro_id} - skipping.")
            continue

        reader = pypdf.PdfReader(str(path))
        cover_text = reader.pages[0].extract_text()
        date_match = _CHMA_DATE_RE.search(cover_text)
        as_of_date = date_match.group(1).strip() if date_match else "unknown"

        for page_number, page in enumerate(reader.pages):
            lines = []
            for line in page.extract_text().split("\n"):
                stripped = line.strip()
                if not stripped or stripped.isdigit():
                    continue
                if any(marker in stripped.lower() for marker in _CHMA_BOILERPLATE_MARKERS):
                    continue
                lines.append(stripped)
            if not lines:
                continue
            chunk_text = "\n".join(lines)
            if len(chunk_text) < 200:  # covers, dividers, near-empty pages
                continue
            section = re.sub(r"\s+\d+$", "", lines[0]).strip()
            db.add(
                MarketCommentaryChunk(
                    metro_id=metro_id,
                    source_file=filename,
                    as_of_date=as_of_date,
                    section=section,
                    page_number=page_number,
                    chunk_text=chunk_text,
                )
            )
            count += 1
    return count


def ingest() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Runs ahead of the "already ingested" guard below so it still
        # fires on a database that already has market metrics loaded -
        # this corpus was added well after the rest and would otherwise
        # never get a chance to run on an existing database.
        if db.query(MarketCommentaryChunk).first() is None:
            chma_count = ingest_hud_chma(db)
            db.commit()
            print(f"Ingested {chma_count} HUD CHMA commentary chunks.")
        else:
            print("HUD CHMA commentary already ingested, skipping.")

        if db.query(MarketMetric).first() is not None:
            print("Market metrics already ingested, skipping.")
            return

        redfin_to_id, aptlist_to_id, income_to_id = load_metros(db)
        print(f"Loaded {len(METRO_CROSSWALK)} metros.")

        redfin_count = ingest_redfin(db, redfin_to_id)
        db.commit()
        print(f"Ingested {redfin_count} Redfin metric rows.")

        aptlist_count = ingest_apartment_list(db, aptlist_to_id)
        db.commit()
        print(f"Ingested {aptlist_count} Apartment List metric rows.")

        income_count = ingest_census_income(db, income_to_id)
        db.commit()
        print(f"Ingested {income_count} Census median household income rows.")

        gross_rent_count = ingest_census_gross_rent_fallback(db)
        db.commit()
        print(f"Ingested {gross_rent_count} Census median gross rent fallback rows.")

        pmms_count = ingest_pmms(db)
        db.commit()
        print(f"Ingested {pmms_count} Freddie Mac PMMS rows.")

        bls_count = ingest_bls_unemployment(db)
        db.commit()
        print(f"Ingested {bls_count} BLS unemployment rate rows.")

        fhfa_count = ingest_fhfa_hpi(db)
        db.commit()
        print(f"Ingested {fhfa_count} FHFA house price index rows.")
    finally:
        db.close()


if __name__ == "__main__":
    ingest()
