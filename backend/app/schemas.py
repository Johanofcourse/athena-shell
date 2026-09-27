import enum
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class MetricName(str, enum.Enum):
    """Every metric actually loaded by ingest_market_data.py. Kept as an
    enum (not a free string) so a malformed or invented metric name from
    the model fails Pydantic validation before it ever reaches a query,
    same reasoning as the old QueryFilters."""

    MEDIAN_SALE_PRICE = "median_sale_price"
    MEDIAN_DAYS_ON_MARKET = "median_days_on_market"
    HOMES_SOLD = "homes_sold"
    NEW_LISTINGS = "new_listings"
    ACTIVE_LISTINGS = "active_listings"
    PENDING_SALES = "pending_sales"
    MEDIAN_PRICE_PER_SQFT = "median_price_per_sqft"
    PRICE_DROP_COUNT = "price_drop_count"
    PRICE_DROP_PCT_AVG = "price_drop_pct_avg"
    PCT_ACTIVE_WITH_PRICE_DROP = "pct_active_with_price_drop"
    HOMES_SOLD_WITH_PRICE_DROP = "homes_sold_with_price_drop"
    TOTAL_DELISTINGS = "total_delistings"
    TOTAL_RELISTINGS = "total_relistings"
    SHARE_DELISTED_PCT = "share_delisted_pct"
    SHARE_RELISTED_PCT = "share_relisted_pct"
    MEDIAN_RENT = "median_rent"
    VACANCY_RATE = "vacancy_rate"
    TIME_ON_MARKET_DAYS = "time_on_market_days"


class MetroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    state: str
    has_sale_data: bool
    has_rent_data: bool


class MarketMetricPoint(BaseModel):
    metro: str
    period: date
    value: float


class MarketQueryFilters(BaseModel):
    """Structured shape every NL query must resolve into. Metros are
    plain strings as the model understands them (e.g. "Austin") -
    resolved against the real Metro table server-side, not assumed to be
    exact - so a typo or an unknown metro is a normal, handled case
    rather than a crash."""

    metros: list[str] = Field(
        default_factory=list,
        description="Metro names mentioned, e.g. ['Austin', 'Denver']. Empty means all metros - used for ranking queries like 'which metro has the biggest price drops'.",
    )
    metric: MetricName
    bed_size: str | None = Field(
        default=None, description="overall, 1br, or 2br - only meaningful for median_rent"
    )
    start_period: str | None = Field(default=None, description="YYYY-MM, inclusive")
    end_period: str | None = Field(default=None, description="YYYY-MM, inclusive")
    sort_by: str = Field(
        default="period",
        description="'period' for a time trend of specific metro(s), 'value' to rank metros by the metric's latest value",
    )
    sort_order: str = Field(default="desc", description="asc or desc")
    limit: int = 60
    unsupported_aspects: list[str] = Field(
        default_factory=list,
        description="Parts of the user's question this schema genuinely cannot answer (e.g. 'school quality', 'crime rate', a specific street address) - name them here instead of silently ignoring them or inventing a filter for them.",
    )


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)


class MarketQueryResponse(BaseModel):
    filters: MarketQueryFilters
    explanation: str
    unmatched_metros: list[str]
    no_data_metros: list[str]
    results: list[MarketMetricPoint]
