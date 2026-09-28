from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Metro
from app.nl_query import _fetch_rent_rows, _query_metric_rows
from app.schemas import MarketMetricPoint, MetricName, MetroOut

router = APIRouter(prefix="/metros", tags=["metros"])


@router.get("", response_model=list[MetroOut])
def list_metros(db: Session = Depends(get_db)) -> list[dict]:
    metros = db.execute(select(Metro).order_by(Metro.canonical_name)).scalars().all()
    return [
        {
            "id": m.id,
            "canonical_name": m.canonical_name,
            "state": m.state,
            "has_sale_data": m.redfin_name is not None,
            "has_rent_data": m.aptlist_name is not None,
            "has_income_data": m.census_income_name is not None,
            "census_gross_rent_county": m.census_gross_rent_county,
        }
        for m in metros
    ]


@router.get("/{metro_id}/series", response_model=list[MarketMetricPoint])
def metro_series(
    metro_id: str,
    metric: MetricName,
    bed_size: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[MarketMetricPoint]:
    metro = db.get(Metro, metro_id)
    if metro is None:
        raise HTTPException(status_code=404, detail="Metro not found")

    # median_rent goes through the same Census gross-rent fallback as the
    # NL query layer, so browsing a metro card and asking about it in
    # natural language never disagree about whether data exists.
    if metric == MetricName.MEDIAN_RENT:
        rows, _used_fallback = _fetch_rent_rows(db, metro, bed_size, None, None)
    else:
        rows = _query_metric_rows(db, metro, metric.value, bed_size, None, None)

    return [MarketMetricPoint(metro=metro.canonical_name, period=r.period, value=r.value) for r in rows]
