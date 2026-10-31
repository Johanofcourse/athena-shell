"""Publishes the dbt pipeline's market_metrics mart into the production-
shaped athena.db SQLite file - scoped to exactly the sources this
pipeline owns (redfin, fema). Every other source's rows (apartment_list,
census, bls, fred, freddie_mac - still written by the existing
backend/app/ingest_market_data.py) are left untouched, as are the live
QueryUsage/QueryFeedback tables this script never even looks at.

Deliberately plain sqlite3 + duckdb, no SQLAlchemy: this script runs in
the pipeline's own lightweight environment (pipeline/requirements.txt),
never installed on the production VM, so it doesn't pull in the backend
app's dependency tree just to write six columns.

Run with: python publish_to_sqlite.py <warehouse.duckdb> <athena.db>
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import duckdb

# Maps the dbt mart's lowercase `source` values to the exact enum member
# NAME SQLAlchemy's Enum column stores in athena.db today - confirmed
# against the real database (SELECT DISTINCT source FROM market_metrics
# returns 'REDFIN', 'FEMA', etc.), not the enum's lowercase .value, which
# a naive guess would reach for and silently write a never-matched row.
SOURCE_TO_ENUM_NAME = {
    "redfin": "REDFIN",
    "fema": "FEMA",
}


def load_mart_rows(warehouse_path: Path) -> list[tuple]:
    con = duckdb.connect(str(warehouse_path), read_only=True)
    try:
        return con.execute(
            "select metro_id, period, source, metric, bed_size, value from market_metrics"
        ).fetchall()
    finally:
        con.close()


def publish(warehouse_path: Path, sqlite_path: Path) -> dict[str, int]:
    rows = load_mart_rows(warehouse_path)
    owned_enum_names = tuple(SOURCE_TO_ENUM_NAME.values())

    conn = sqlite3.connect(str(sqlite_path))
    try:
        placeholders = ",".join("?" for _ in owned_enum_names)
        cur = conn.execute(
            f"DELETE FROM market_metrics WHERE source IN ({placeholders})", owned_enum_names
        )
        deleted = cur.rowcount

        for metro_id, period, source, metric, bed_size, value in rows:
            conn.execute(
                "INSERT INTO market_metrics (metro_id, period, source, metric, bed_size, value) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (metro_id, period.isoformat(), SOURCE_TO_ENUM_NAME[source], metric, bed_size, value),
            )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"deleted": deleted, "inserted": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("warehouse_path", type=Path, help="Path to the dbt-built warehouse.duckdb")
    parser.add_argument("sqlite_path", type=Path, help="Path to the existing production-shaped athena.db")
    args = parser.parse_args()

    if not args.sqlite_path.exists():
        sys.exit(
            f"{args.sqlite_path} does not exist. This script replaces rows in an existing "
            "athena.db (fetched from production) - it never creates one from scratch."
        )

    stats = publish(args.warehouse_path, args.sqlite_path)
    print(f"Deleted {stats['deleted']} existing redfin/fema rows, inserted {stats['inserted']} fresh rows.")


if __name__ == "__main__":
    main()
