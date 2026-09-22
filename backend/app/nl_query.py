import json

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Listing, ListingStatus
from app.schemas import QueryFilters

SYSTEM_PROMPT = """You translate a home-buyer's natural-language question about a real estate \
listing-history dataset into a structured filter call. Always call filter_listings exactly once. \
Only set fields the question actually implies - leave everything else null. Today's context: the \
dataset covers the trailing 12 months of listing activity across the covered metro areas."""

FILTER_LISTINGS_TOOL = {
    "type": "function",
    "function": {
        "name": "filter_listings",
        "description": "Filter and sort the real estate listing-history dataset.",
        "parameters": {
            "type": "object",
            "properties": {
                "min_price": {"type": "number"},
                "max_price": {"type": "number"},
                "city": {"type": "string"},
                "state": {"type": "string", "description": "Two-letter state code"},
                "property_type": {
                    "type": "string",
                    "description": "e.g. single_family, condo, townhouse, multi_family",
                },
                "bedrooms_min": {"type": "integer"},
                "bathrooms_min": {"type": "number"},
                "min_price_drop_pct": {
                    "type": "number",
                    "description": "Minimum percent drop from original list price, e.g. 5 for 5%",
                },
                "min_price_drop_amount": {"type": "number"},
                "min_days_on_market": {"type": "integer"},
                "max_days_on_market": {"type": "integer"},
                "min_relist_count": {
                    "type": "integer",
                    "description": "Minimum number of times the listing was taken off and relisted",
                },
                "status": {
                    "type": "string",
                    "enum": [s.value for s in ListingStatus],
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["price", "days_on_market", "price_drop_pct", "relist_count"],
                },
                "sort_order": {"type": "string", "enum": ["asc", "desc"]},
                "limit": {"type": "integer", "description": "Defaults to 25, max 200"},
            },
            "additionalProperties": False,
        },
    },
}


def _client() -> OpenAI:
    return OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)


def interpret_query(query: str) -> QueryFilters:
    response = _client().chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        tools=[FILTER_LISTINGS_TOOL],
        tool_choice={"type": "function", "function": {"name": "filter_listings"}},
    )

    message = response.choices[0].message
    if not message.tool_calls:
        return QueryFilters()

    raw_args = message.tool_calls[0].function.arguments
    try:
        parsed = json.loads(raw_args)
    except json.JSONDecodeError:
        return QueryFilters()

    return QueryFilters.model_validate(parsed)


def explain_filters(filters: QueryFilters) -> str:
    """Built from the resolved filter object rather than a second model call -
    deterministic, free, and can't drift from what actually ran."""
    parts: list[str] = []

    if filters.city or filters.state:
        location = ", ".join(p for p in [filters.city, filters.state] if p)
        parts.append(f"in {location}")
    if filters.property_type:
        parts.append(f"property type {filters.property_type}")
    if filters.bedrooms_min:
        parts.append(f"{filters.bedrooms_min}+ bedrooms")
    if filters.bathrooms_min:
        parts.append(f"{filters.bathrooms_min}+ bathrooms")
    if filters.min_price or filters.max_price:
        lo = f"${filters.min_price:,.0f}" if filters.min_price else "any"
        hi = f"${filters.max_price:,.0f}" if filters.max_price else "any"
        parts.append(f"price between {lo} and {hi}")
    if filters.min_price_drop_pct:
        parts.append(f"price dropped at least {filters.min_price_drop_pct:g}%")
    if filters.min_price_drop_amount:
        parts.append(f"price dropped at least ${filters.min_price_drop_amount:,.0f}")
    if filters.min_days_on_market:
        parts.append(f"on market {filters.min_days_on_market}+ days")
    if filters.max_days_on_market:
        parts.append(f"on market under {filters.max_days_on_market} days")
    if filters.min_relist_count:
        parts.append(f"relisted {filters.min_relist_count}+ times")
    if filters.status:
        parts.append(f"status = {filters.status.value}")

    if not parts:
        return "No specific filters were detected, showing recent listings."

    summary = "Showing listings " + ", ".join(parts)
    if filters.sort_by:
        summary += f", sorted by {filters.sort_by} ({filters.sort_order or 'desc'})"
    return summary + "."


def apply_filters(db: Session, filters: QueryFilters) -> list[Listing]:
    stmt = select(Listing)

    if filters.min_price is not None:
        stmt = stmt.where(Listing.current_price >= filters.min_price)
    if filters.max_price is not None:
        stmt = stmt.where(Listing.current_price <= filters.max_price)
    if filters.city:
        stmt = stmt.where(Listing.city.ilike(filters.city))
    if filters.state:
        stmt = stmt.where(Listing.state.ilike(filters.state))
    if filters.property_type:
        stmt = stmt.where(Listing.property_type.ilike(filters.property_type))
    if filters.bedrooms_min is not None:
        stmt = stmt.where(Listing.bedrooms >= filters.bedrooms_min)
    if filters.bathrooms_min is not None:
        stmt = stmt.where(Listing.bathrooms >= filters.bathrooms_min)
    if filters.min_price_drop_pct is not None:
        stmt = stmt.where(Listing.price_drop_pct >= filters.min_price_drop_pct)
    if filters.min_price_drop_amount is not None:
        stmt = stmt.where(Listing.price_drop_amount >= filters.min_price_drop_amount)
    if filters.min_days_on_market is not None:
        stmt = stmt.where(Listing.days_on_market >= filters.min_days_on_market)
    if filters.max_days_on_market is not None:
        stmt = stmt.where(Listing.days_on_market <= filters.max_days_on_market)
    if filters.min_relist_count is not None:
        stmt = stmt.where(Listing.relist_count >= filters.min_relist_count)
    if filters.status is not None:
        stmt = stmt.where(Listing.status == filters.status)

    sort_column = {
        "price": Listing.current_price,
        "days_on_market": Listing.days_on_market,
        "price_drop_pct": Listing.price_drop_pct,
        "relist_count": Listing.relist_count,
    }.get(filters.sort_by or "", Listing.last_event_date)
    stmt = stmt.order_by(sort_column.desc() if (filters.sort_order or "desc") == "desc" else sort_column.asc())

    limit = max(1, min(filters.limit or 25, 200))
    stmt = stmt.limit(limit)

    return list(db.execute(stmt).scalars().all())
