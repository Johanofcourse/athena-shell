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
    MEDIAN_HOUSEHOLD_INCOME = "median_household_income"
    RENT_TO_INCOME_PCT = "rent_to_income_pct"
    UNEMPLOYMENT_RATE = "unemployment_rate"
    HOUSE_PRICE_INDEX = "house_price_index"
    # Not user-selectable (excluded from the tool schema's enum) - an
    # internal fallback value substituted into median_rent results for the
    # 10 metro-division metros Apartment List doesn't cover, always
    # returned under this distinct name so it's never confused with real
    # median_rent data. See run_market_query.
    MEDIAN_GROSS_RENT = "median_gross_rent"
    # National series, no metro dimension - metros is always sanitized to
    # empty for these (see _sanitize_filters). Points are labeled
    # "United States" rather than a real Metro.
    MORTGAGE_RATE_30YR_FIXED = "mortgage_rate_30yr_fixed"
    MORTGAGE_RATE_15YR_FIXED = "mortgage_rate_15yr_fixed"
    MORTGAGE_RATE_5_1_ARM = "mortgage_rate_5_1_arm"


class MetroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    state: str
    has_sale_data: bool
    has_rent_data: bool
    has_income_data: bool
    census_gross_rent_county: str | None
    latitude: float
    longitude: float


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


class ConversationTurn(BaseModel):
    """One prior turn, as sent back by the client. The client is the only
    place conversation state lives - there's no server-side session store -
    so it resends the turns it wants remembered on every request."""

    query: str = Field(min_length=1, max_length=300)
    filters: MarketQueryFilters


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    history: list[ConversationTurn] = Field(
        default_factory=list,
        max_length=5,  # bounds how much context (and DeepSeek cost) one request can carry
    )


class CommentaryQuery(BaseModel):
    """search_market_commentary's resolved arguments - the commentary-tool
    counterpart to MarketQueryFilters. Deliberately a separate, much
    smaller shape rather than reusing MarketQueryFilters: a "why" question
    about one metro has nothing in common with a metric/period/sort
    specification, and forcing it into that shape would mean most of
    MarketQueryFilters' fields are meaningless noise on every commentary
    call."""

    metro: str = Field(description="The single metro name the question is about, e.g. 'Austin'.")
    topic: str = Field(description="Short keyword phrase capturing what the question is actually about.")


class CommentaryChunkOut(BaseModel):
    section: str
    text: str


class MarketCommentaryResult(BaseModel):
    """A retrieved HUD CHMA excerpt answering a "why" question about one
    metro - strictly separate from MarketQueryResponse.results (the exact
    numeric answer), never blended into it, same honesty principle as the
    approximated_metros fallback. as_of_date is the report's own stated
    date, always shown, so a real but possibly old explanation (see
    los-angeles-ca in HUD_CHMA_FILES) is never presented as current."""

    metro: str
    as_of_date: str
    source_file: str
    chunks: list[CommentaryChunkOut]


class MarketQueryResponse(BaseModel):
    # None exactly when this is a commentary response (commentary is set
    # instead) - a "why" question never resolves to a metric/period/sort
    # specification, so there's nothing honest to put here for that case.
    filters: MarketQueryFilters | None
    explanation: str
    unmatched_metros: list[str]
    no_data_metros: list[str]
    approximated_metros: list[str]
    results: list[MarketMetricPoint]
    commentary: MarketCommentaryResult | None = None


class FeedbackRequest(BaseModel):
    """The frontend resends the original query and the exact filters it
    was shown, rather than referencing a stored request by ID - there's
    no session/request store to reference, and this keeps feedback
    self-contained: the row alone tells a later reviewer everything
    needed to judge whether the rating was fair."""

    query: str = Field(min_length=1, max_length=300)
    filters: MarketQueryFilters
    rating: str = Field(pattern="^(up|down)$")
