"""Loads the real Redfin + Apartment List market data (see
docs/ROADMAP.md Phase 3) into the Metro/MarketMetric tables.

Run with: python -m app.ingest_market_data
"""

import csv
from datetime import date
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.market_crosswalk import METRO_CROSSWALK
from app.models import MarketMetric, MetricSource, Metro

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


def ingest() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
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
    finally:
        db.close()


if __name__ == "__main__":
    ingest()
