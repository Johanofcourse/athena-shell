import enum
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Metro(Base):
    """A metro area, the geography unit for the real market-trend data
    (Phase 3). Redfin, Apartment List, and Census name the same metro
    differently (and Redfin sometimes tracks a metropolitan *division* -
    e.g. Anaheim - that Apartment List and Census's metro-level tables
    only publish as part of a larger combined metro - e.g. Los Angeles),
    so this table is also the crosswalk: each source's native name is
    stored alongside the canonical one. A metro missing aptlist_name or
    census_income_name genuinely has no data at this granularity from
    that source - a real gap, not something to paper over by borrowing a
    parent metro's numbers. (The one exception, deliberately narrower:
    median_gross_rent, ingested from Census's county-level table for
    exactly those metro-division metros, as an explicitly flagged
    approximation of median_rent - see run_market_query.)"""

    __tablename__ = "metros"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # slug, e.g. "austin-tx"
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, index=True)

    redfin_name: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    aptlist_name: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    census_income_name: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    # The specific county backing the median_gross_rent fallback (e.g.
    # "Orange County, California" for Anaheim) - set only for the 10
    # metro-division metros, so the caveat can name exactly what's being
    # shown instead of a generic "Census data" gesture.
    census_gross_rent_county: Mapped[str | None] = mapped_column(String, nullable=True)

    metrics: Mapped[list["MarketMetric"]] = relationship(back_populates="metro")


class MetricSource(str, enum.Enum):
    REDFIN = "redfin"
    APARTMENT_LIST = "apartment_list"
    CENSUS = "census"
    FREDDIE_MAC = "freddie_mac"
    BLS = "bls"
    FRED = "fred"


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


class NationalMetric(Base):
    """One (period, metric) observation with no metro dimension at all -
    for genuinely national series like Freddie Mac's mortgage rates.
    Deliberately a separate table from MarketMetric rather than a fake
    "United States" row in Metro: a national rate isn't a per-metro fact,
    and forcing it into the metro crosswalk would show up oddly in the
    metro browsing grid. period is the real reported date (weekly for
    PMMS), not bucketed to first-of-month like MarketMetric - there's no
    reason to throw away real granularity the source actually reports at."""

    __tablename__ = "national_metrics"
    __table_args__ = (UniqueConstraint("period", "source", "metric", name="uq_national_metric"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    period: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[MetricSource] = mapped_column(Enum(MetricSource), nullable=False)
    metric: Mapped[str] = mapped_column(String, nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)


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


class MarketCommentaryChunk(Base):
    """One section of one HUD Comprehensive Housing Market Analysis (CHMA)
    report, for the search_market_commentary tool (Phase 8) - the "why"
    counterpart to query_market_metrics' "what". Deliberately one row per
    PDF page rather than a fixed-size text window: these reports are
    already organized into clear named sections (Economic Conditions,
    Population and Households, Home Sales Market, ...) that map one-to-one
    onto pages, so page-level chunking preserves real document structure
    instead of cutting mid-thought. as_of_date is the report's own stated
    date (extracted from its text, not inferred from the filename), since
    that's the real honesty-relevant fact here - a 2013 report cited
    without its date would misrepresent itself as current. No embedding
    column: ranking happens in-process via TF-IDF over one metro's chunks
    at query time (a few dozen short chunks per metro), not a precomputed
    vector index - more infrastructure than this corpus size would ever
    need. See ROADMAP.md Phase 8 for the full reasoning, including why a
    local embedding model was considered and set aside in favor of this."""

    __tablename__ = "market_commentary_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metro_id: Mapped[str] = mapped_column(ForeignKey("metros.id"), nullable=False, index=True)

    source_file: Mapped[str] = mapped_column(String, nullable=False)
    as_of_date: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "January 1, 2022" - the report's own text, not reformatted
    section: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "Economic Conditions"
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(String, nullable=False)

    metro: Mapped["Metro"] = relationship()


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
