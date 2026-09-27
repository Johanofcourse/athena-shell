import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ListingStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    OFF_MARKET = "off_market"


class EventType(str, enum.Enum):
    LISTED = "listed"
    PRICE_CHANGE = "price_change"
    STATUS_CHANGE = "status_change"
    RELISTED = "relisted"
    DELISTED = "delisted"
    SOLD = "sold"


class Listing(Base):
    """A property. Denormalized summary fields (current_price, days_on_market,
    relist_count, ...) are derived from this listing's events and kept in sync
    by the seed/ingestion step, so the query layer can filter/sort on them
    without recomputing history on every request."""

    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    address: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String, nullable=False, index=True)
    zip_code: Mapped[str] = mapped_column(String, nullable=False)

    property_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[float] = mapped_column(Float, nullable=False)
    sqft: Mapped[int] = mapped_column(Integer, nullable=False)

    first_listed_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_event_date: Mapped[date] = mapped_column(Date, nullable=False)

    original_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_drop_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    price_drop_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus), nullable=False, default=ListingStatus.ACTIVE, index=True
    )
    days_on_market: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_days_on_market: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relist_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events: Mapped[list["ListingEvent"]] = relationship(
        back_populates="listing", order_by="ListingEvent.event_date", cascade="all, delete-orphan"
    )


class ListingEvent(Base):
    """One append-only entry in a listing's history timeline."""

    __tablename__ = "listing_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), nullable=False, index=True)

    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[ListingStatus | None] = mapped_column(Enum(ListingStatus), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    listing: Mapped["Listing"] = relationship(back_populates="events")


class Metro(Base):
    """A metro area, the geography unit for the real market-trend data
    (Phase 3). Redfin and Apartment List name the same metro differently
    (and Redfin sometimes tracks a metropolitan *division* - e.g. Anaheim -
    that Apartment List only publishes as part of a larger combined metro -
    e.g. Los Angeles), so this table is also the crosswalk: each source's
    native name is stored alongside the canonical one. A metro missing
    aptlist_name genuinely has no rent-side data at this granularity -
    that's a real gap, not something to paper over by borrowing a parent
    metro's numbers."""

    __tablename__ = "metros"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # slug, e.g. "austin-tx"
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, index=True)

    redfin_name: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    aptlist_name: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)

    metrics: Mapped[list["MarketMetric"]] = relationship(back_populates="metro")


class MetricSource(str, enum.Enum):
    REDFIN = "redfin"
    APARTMENT_LIST = "apartment_list"


class MarketMetric(Base):
    """One (metro, period, metric) observation. A long/tidy fact table
    rather than one wide column per metric: new metrics or sources add
    rows, never a migration, and the NL query layer only ever needs to
    reason about "metric X for metro Y over period range Z" regardless of
    which source it came from."""

    __tablename__ = "market_metrics"
    __table_args__ = (
        UniqueConstraint("metro_id", "period", "source", "metric", "bed_size", name="uq_market_metric"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metro_id: Mapped[str] = mapped_column(ForeignKey("metros.id"), nullable=False, index=True)

    period: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # first-of-month
    source: Mapped[MetricSource] = mapped_column(Enum(MetricSource), nullable=False)
    metric: Mapped[str] = mapped_column(String, nullable=False, index=True)
    bed_size: Mapped[str | None] = mapped_column(String, nullable=True)  # "overall"/"1br"/"2br", rent metrics only
    value: Mapped[float] = mapped_column(Float, nullable=False)

    metro: Mapped["Metro"] = relationship(back_populates="metrics")
