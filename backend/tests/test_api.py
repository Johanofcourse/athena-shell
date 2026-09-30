"""API contract tests via FastAPI's TestClient, against the synthetic
seeded_db fixture (never the real athena.db) through a get_db dependency
override.

Deliberately does NOT test POST /query - that requires a live DeepSeek
key and is exactly what the eval suite (backend/evals/) already covers,
run manually rather than in CI (see docs/PRODUCT_REVIEW.md /
feedback_eval_suite_cadence). This file covers the plain-read/write
endpoints that don't touch the LLM.
"""

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import QueryFeedback


def _client_for(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client


def test_health():
    client = _client_for_noop()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    app.dependency_overrides.clear()


def _client_for_noop():
    # /health doesn't touch the db at all, but TestClient still runs the
    # startup event against the real engine - harmless (idempotent
    # create_all), just noting it rather than hiding it.
    return TestClient(app)


def test_list_metros_shape_and_flags(seeded_db, monkeypatch):
    # METRO_COORDINATES is a static dict keyed by the 50 real metro ids -
    # genuinely never missing an entry for a real ingested Metro (see
    # test_crosswalk.py), but the synthetic fixture metros here aren't in
    # it, so the router needs fake coordinates for them specifically.
    from app.routers import metros as metros_router

    monkeypatch.setattr(
        metros_router,
        "METRO_COORDINATES",
        {"testville-ts": (30.0, -97.0), "gapford-gf": (33.8, -117.8), "emptyburg-eb": (0.0, 0.0)},
    )

    client = _client_for(seeded_db)
    try:
        resp = client.get("/metros")
        assert resp.status_code == 200
        by_id = {m["id"]: m for m in resp.json()}
        assert set(by_id) == {"testville-ts", "gapford-gf", "emptyburg-eb"}

        testville = by_id["testville-ts"]
        assert testville["has_sale_data"] is True
        assert testville["has_rent_data"] is True
        assert testville["has_income_data"] is True
        assert testville["census_gross_rent_county"] is None
        assert testville["latitude"] == 30.0
        assert testville["longitude"] == -97.0

        gapford = by_id["gapford-gf"]
        assert gapford["has_rent_data"] is False
        assert gapford["has_income_data"] is False
        assert gapford["census_gross_rent_county"] == "Gap County, GF"
    finally:
        app.dependency_overrides.clear()


def test_metro_series_real_metric(seeded_db):
    client = _client_for(seeded_db)
    try:
        resp = client.get("/metros/testville-ts/series", params={"metric": "median_sale_price"})
        assert resp.status_code == 200
        points = resp.json()
        assert len(points) == 1
        assert points[0]["value"] == 300000.0
    finally:
        app.dependency_overrides.clear()


def test_metro_series_rent_uses_fallback_for_gap_metro(seeded_db):
    # Confirms the router itself (not just the underlying function in
    # isolation) applies the median_rent -> median_gross_rent fallback -
    # this is the exact code path the metro detail panel calls.
    client = _client_for(seeded_db)
    try:
        resp = client.get("/metros/gapford-gf/series", params={"metric": "median_rent", "bed_size": "overall"})
        assert resp.status_code == 200
        points = resp.json()
        assert len(points) == 1
        assert points[0]["value"] == 1800.0
    finally:
        app.dependency_overrides.clear()


def test_metro_series_unknown_metro_404(seeded_db):
    client = _client_for(seeded_db)
    try:
        resp = client.get("/metros/nowhere-xx/series", params={"metric": "median_sale_price"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_submit_feedback_persists_row(seeded_db):
    client = _client_for(seeded_db)
    try:
        payload = {
            "query": "What's the median sale price in Testville?",
            "filters": {
                "metros": ["Testville, TS"],
                "metric": "median_sale_price",
                "bed_size": None,
                "start_period": None,
                "end_period": None,
                "sort_by": "period",
                "sort_order": "desc",
                "limit": 60,
                "unsupported_aspects": [],
            },
            "rating": "up",
        }
        resp = client.post("/query/feedback", json=payload)
        assert resp.status_code == 204

        row = seeded_db.query(QueryFeedback).one()
        assert row.query == payload["query"]
        assert row.rating.value == "up"
        assert row.filters["metric"] == "median_sale_price"
    finally:
        app.dependency_overrides.clear()


def test_submit_feedback_rejects_invalid_rating(seeded_db):
    client = _client_for(seeded_db)
    try:
        payload = {
            "query": "test",
            "filters": {"metros": [], "metric": "median_sale_price"},
            "rating": "sideways",
        }
        resp = client.post("/query/feedback", json=payload)
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()
