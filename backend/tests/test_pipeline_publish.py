"""Tests for pipeline/scripts/publish_to_sqlite.py - the step that
copies the dbt pipeline's market_metrics mart into a production-shaped
athena.db. Same fixture conventions as test_ingest.py: a throwaway
SQLite file under tmp_path, synthetic metros, never the real dev
athena.db. The "warehouse" here is a tiny fixture DuckDB file, not a
real dbt build - these tests exercise the publish script itself, not
dbt.
"""

import importlib.util
import sqlite3
from datetime import date
from pathlib import Path

import duckdb
import pytest
from sqlalchemy import create_engine

from app.database import Base
from app.models import MarketMetric, MetricSource, Metro

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISH_SCRIPT_PATH = REPO_ROOT / "pipeline" / "scripts" / "publish_to_sqlite.py"

_spec = importlib.util.spec_from_file_location("publish_to_sqlite", PUBLISH_SCRIPT_PATH)
publish_to_sqlite = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(publish_to_sqlite)


@pytest.fixture()
def athena_db_path(tmp_path) -> Path:
    """A throwaway, production-shaped SQLite file - same schema as the
    real athena.db, pre-seeded with rows from sources this pipeline does
    NOT own (apartment_list, census) plus stale redfin/fema rows that a
    prior pipeline run should have since replaced."""
    db_path = tmp_path / "athena.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(
            Metro.__table__.insert(),
            [{"id": "testville-ts", "canonical_name": "Testville, TS", "state": "TS"}],
        )
        conn.execute(
            MarketMetric.__table__.insert(),
            [
                # Owned by this pipeline - stale, should be deleted.
                {
                    "metro_id": "testville-ts",
                    "period": date(2020, 1, 1),
                    "source": MetricSource.REDFIN,
                    "metric": "homes_sold",
                    "bed_size": None,
                    "value": 1.0,
                },
                # NOT owned by this pipeline - must survive untouched.
                {
                    "metro_id": "testville-ts",
                    "period": date(2024, 1, 1),
                    "source": MetricSource.APARTMENT_LIST,
                    "metric": "median_rent",
                    "bed_size": "overall",
                    "value": 2000.0,
                },
                {
                    "metro_id": "testville-ts",
                    "period": date(2024, 1, 1),
                    "source": MetricSource.CENSUS,
                    "metric": "median_household_income",
                    "bed_size": None,
                    "value": 100000.0,
                },
            ],
        )
        conn.commit()
    engine.dispose()
    return db_path


@pytest.fixture()
def warehouse_path(tmp_path) -> Path:
    """A tiny fixture DuckDB file shaped like the real market_metrics
    mart - two fresh rows, one per source this pipeline owns."""
    db_path = tmp_path / "warehouse.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute(
        "create table market_metrics (metro_id varchar, period date, source varchar, "
        "metric varchar, bed_size varchar, value double)"
    )
    con.execute(
        "insert into market_metrics values "
        "('testville-ts', '2025-06-01', 'redfin', 'homes_sold', NULL, 42.0), "
        "('testville-ts', '2025-12-01', 'fema', 'natural_hazard_risk_score', NULL, 55.5)"
    )
    con.close()
    return db_path


def _read_rows(sqlite_path: Path) -> list[tuple]:
    conn = sqlite3.connect(str(sqlite_path))
    try:
        return conn.execute(
            "select metro_id, period, source, metric, bed_size, value from market_metrics order by source, metric"
        ).fetchall()
    finally:
        conn.close()


def test_publish_replaces_only_owned_sources(athena_db_path, warehouse_path):
    stats = publish_to_sqlite.publish(warehouse_path, athena_db_path)

    assert stats == {"deleted": 1, "inserted": 2}

    rows = _read_rows(athena_db_path)
    assert rows == [
        ("testville-ts", "2024-01-01", "APARTMENT_LIST", "median_rent", "overall", 2000.0),
        ("testville-ts", "2024-01-01", "CENSUS", "median_household_income", None, 100000.0),
        ("testville-ts", "2025-12-01", "FEMA", "natural_hazard_risk_score", None, 55.5),
        ("testville-ts", "2025-06-01", "REDFIN", "homes_sold", None, 42.0),
    ]


def test_publish_is_idempotent(athena_db_path, warehouse_path):
    publish_to_sqlite.publish(warehouse_path, athena_db_path)
    second_stats = publish_to_sqlite.publish(warehouse_path, athena_db_path)

    # The second run deletes exactly what the first run inserted - no
    # duplicates accumulate across repeated scheduled runs.
    assert second_stats == {"deleted": 2, "inserted": 2}
    rows = _read_rows(athena_db_path)
    assert len(rows) == 4


def test_publish_refuses_to_create_a_fresh_db(tmp_path, warehouse_path, monkeypatch):
    missing_path = tmp_path / "does-not-exist.db"
    monkeypatch.setattr(
        "sys.argv", ["publish_to_sqlite.py", str(warehouse_path), str(missing_path)]
    )

    with pytest.raises(SystemExit):
        publish_to_sqlite.main()

    assert not missing_path.exists()
