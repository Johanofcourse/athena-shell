"""Shared fixtures for the backend test suite.

Every test gets its own throwaway SQLite file (via pytest's tmp_path),
never the real dev athena.db - these tests insert synthetic, clearly-fake
metros (Testville, Gapford, Emptyburg) rather than reusing real metro
names, so a failure or a stray print can never be mistaken for a real
data problem.
"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import MarketMetric, MetricSource, Metro

# Deliberately round numbers so ratio/percent math in tests is exact,
# not approximately-equal-with-a-tolerance.
TESTVILLE_RENT_JAN = 2000.0
TESTVILLE_RENT_FEB = 2100.0
TESTVILLE_INCOME = 100000.0
GAPFORD_GROSS_RENT = 1800.0


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _add_metric(db, metro_id, metric, value, period, source, bed_size=None):
    db.add(
        MarketMetric(
            metro_id=metro_id,
            period=period,
            source=source,
            metric=metric,
            bed_size=bed_size,
            value=value,
        )
    )


@pytest.fixture()
def seeded_db(db_session):
    """Three synthetic metros covering the three cases that matter for the
    rent-fallback / income / rent-to-income logic:

    - testville-ts: full coverage (sale, rent at all bed sizes, income) -
      the "normal" case, with two rent periods so trend math is checkable.
    - gapford-gf: a metro-division gap metro *with* the Census gross-rent
      fallback (mirrors Anaheim/Fort Worth/etc.) - has sale data and a
      county-level median_gross_rent row, but no aptlist rent and no
      census income at all (the real gap is narrower than the rent
      fallback, on purpose - see ingest_market_data.py).
    - emptyburg-eb: has sale data only - no rent, no fallback, no income -
      to distinguish "fallback exists" from "genuinely nothing exists".
    """
    db_session.add(
        Metro(
            id="testville-ts",
            canonical_name="Testville, TS",
            state="TS",
            redfin_name="Testville, TS metro area",
            aptlist_name="Testville, TS",
            census_income_name="Testville, TS Metro Area",
            census_gross_rent_county=None,
        )
    )
    db_session.add(
        Metro(
            id="gapford-gf",
            canonical_name="Gapford, GF",
            state="GF",
            redfin_name="Gapford, GF metro area",
            aptlist_name=None,
            census_income_name=None,
            census_gross_rent_county="Gap County, GF",
        )
    )
    db_session.add(
        Metro(
            id="emptyburg-eb",
            canonical_name="Emptyburg, EB",
            state="EB",
            redfin_name="Emptyburg, EB metro area",
            aptlist_name=None,
            census_income_name=None,
            census_gross_rent_county=None,
        )
    )
    db_session.flush()

    _add_metric(db_session, "testville-ts", "median_sale_price", 300000, date(2024, 1, 1), MetricSource.REDFIN)
    _add_metric(
        db_session, "testville-ts", "median_rent", TESTVILLE_RENT_JAN, date(2024, 1, 1),
        MetricSource.APARTMENT_LIST, bed_size="overall",
    )
    _add_metric(
        db_session, "testville-ts", "median_rent", TESTVILLE_RENT_FEB, date(2024, 2, 1),
        MetricSource.APARTMENT_LIST, bed_size="overall",
    )
    _add_metric(
        db_session, "testville-ts", "median_rent", 1500, date(2024, 1, 1),
        MetricSource.APARTMENT_LIST, bed_size="1br",
    )
    _add_metric(
        db_session, "testville-ts", "median_household_income", TESTVILLE_INCOME, date(2024, 1, 1),
        MetricSource.CENSUS,
    )

    _add_metric(db_session, "gapford-gf", "median_sale_price", 250000, date(2024, 1, 1), MetricSource.REDFIN)
    _add_metric(
        db_session, "gapford-gf", "median_gross_rent", GAPFORD_GROSS_RENT, date(2024, 1, 1), MetricSource.CENSUS
    )

    _add_metric(db_session, "emptyburg-eb", "median_sale_price", 200000, date(2024, 1, 1), MetricSource.REDFIN)

    db_session.commit()
    return db_session
