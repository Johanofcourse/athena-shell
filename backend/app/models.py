import enum
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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


class QueryUsage(Base):
    """Persistent per-IP, per-day query count for the free-tier cap on
    POST /query - distinct from the slowapi burst limiter (which resets
    every minute and only guards against rapid-fire abuse). This is a
    cumulative daily quota, and it's the first piece of what Phase 7
    (real accounts/payments) will eventually build tier enforcement on
    top of - not throwaway work."""

    __tablename__ = "query_usage"

    ip: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FeedbackRating(str, enum.Enum):
    UP = "up"
    DOWN = "down"


class QueryFeedback(Base):
    """One user rating on one query's interpretation - the raw material
    for turning real production usage into eval growth over time, per the
    ROADMAP goal. Stores the natural-language query and the exact
    resolved filters (not just a foreign key to a request we don't
    otherwise persist), so a later review pass can see both the question
    and what the model did with it without needing anything else."""

    __tablename__ = "query_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String, nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False)
    rating: Mapped[FeedbackRating] = mapped_column(Enum(FeedbackRating), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
