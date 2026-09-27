from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MarketMetric, Metro
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

    stmt = select(MarketMetric).where(
        MarketMetric.metro_id == metro_id,
        MarketMetric.metric == metric.value,
    )
    if bed_size:
        stmt = stmt.where(MarketMetric.bed_size == bed_size)
    stmt = stmt.order_by(MarketMetric.period.asc())

    rows = db.execute(stmt).scalars().all()
    return [MarketMetricPoint(metro=metro.canonical_name, period=r.period, value=r.value) for r in rows]
