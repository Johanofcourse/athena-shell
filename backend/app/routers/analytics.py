from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Metro
from app.nl_query import latest_metric_value
from app.schemas import MetricName, MetroSnapshot

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Metrics realistically comparable across all 50 metros at a single
# snapshot - excludes the 3 national mortgage-rate series (no metro
# dimension) and rent_to_income_pct (a derived ratio the frontend computes
# itself from median_rent + median_household_income, see analytics.ts).
SNAPSHOT_METRICS = [
    MetricName.MEDIAN_SALE_PRICE,
    MetricName.MEDIAN_DAYS_ON_MARKET,
    MetricName.ACTIVE_LISTINGS,
    MetricName.PCT_ACTIVE_WITH_PRICE_DROP,
    MetricName.MEDIAN_PRICE_PER_SQFT,
    MetricName.MEDIAN_RENT,
    MetricName.VACANCY_RATE,
    MetricName.MEDIAN_HOUSEHOLD_INCOME,
    MetricName.UNEMPLOYMENT_RATE,
    MetricName.MEAN_COMMUTE_MINUTES,
    MetricName.MEDIAN_PROPERTY_TAX,
    MetricName.TOTAL_POPULATION,
    MetricName.HOUSE_PRICE_INDEX,
    MetricName.NATURAL_HAZARD_RISK_SCORE,
]


@router.get("/snapshot", response_model=list[MetroSnapshot])
def snapshot(db: Session = Depends(get_db)) -> list[MetroSnapshot]:
    metros = list(db.execute(select(Metro).order_by(Metro.canonical_name)).scalars().all())
    out: list[MetroSnapshot] = []
    for metro in metros:
        values: dict[str, float] = {}
        for metric in SNAPSHOT_METRICS:
            latest = latest_metric_value(db, metro, metric)
            if latest is not None:
                values[metric.value] = latest.value
        out.append(MetroSnapshot(metro=metro.canonical_name, state=metro.state, values=values))
    return out
