import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String
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
