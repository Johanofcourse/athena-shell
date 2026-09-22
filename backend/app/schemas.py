from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models import EventType, ListingStatus


class ListingEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_type: EventType
    event_date: date
    price: float | None
    status: ListingStatus | None
    notes: str | None


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: str
    bedrooms: int
    bathrooms: float
    sqft: int
    first_listed_date: date
    last_event_date: date
    original_price: float
    current_price: float
    price_drop_amount: float
    price_drop_pct: float
    status: ListingStatus
    days_on_market: int
    total_days_on_market: int
    relist_count: int


class ListingDetailOut(ListingOut):
    events: list[ListingEventOut]


class QueryFilters(BaseModel):
    """Structured filter shape the NL layer must resolve every query into.
    Kept intentionally flat/predefined (rather than free-form SQL) so results
    are always produced by a safe, testable query path."""

    min_price: float | None = None
    max_price: float | None = None
    city: str | None = None
    state: str | None = None
    property_type: str | None = None
    bedrooms_min: int | None = None
    bathrooms_min: float | None = None
    min_price_drop_pct: float | None = None
    min_price_drop_amount: float | None = None
    min_days_on_market: int | None = None
    max_days_on_market: int | None = None
    min_relist_count: int | None = None
    status: ListingStatus | None = None
    sort_by: str | None = Field(
        default=None,
        description="One of: price, days_on_market, price_drop_pct, relist_count",
    )
    sort_order: str | None = Field(default="desc", description="asc or desc")
    limit: int = 25


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)


class QueryResponse(BaseModel):
    filters: QueryFilters
    explanation: str
    results: list[ListingOut]
