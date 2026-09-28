from fastapi import APIRouter, Depends, HTTPException, Request
from openai import APIError
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import FeedbackRating, QueryFeedback
from app.nl_query import explain_filters, interpret_query, run_market_query
from app.rate_limit import limiter
from app.schemas import FeedbackRequest, MarketQueryResponse, QueryRequest
from app.usage import FREE_DAILY_QUERY_LIMIT, check_and_increment_usage

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=MarketQueryResponse)
@limiter.limit("10/minute")
def run_query(request: Request, payload: QueryRequest, db: Session = Depends(get_db)) -> MarketQueryResponse:
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=503,
            detail="DEEPSEEK_API_KEY is not configured on the server.",
        )

    # Checked before the (paid) DeepSeek call, not after - a rejected
    # request shouldn't still cost an API call.
    allowed, _remaining = check_and_increment_usage(db, get_remote_address(request))
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"You've used today's free {FREE_DAILY_QUERY_LIMIT} queries. This resets tomorrow (UTC).",
        )

    try:
        filters = interpret_query(payload.query, payload.history)
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek API error: {exc}") from exc

    results, unmatched_metros, no_data_metros = run_market_query(db, filters)
    explanation = explain_filters(filters, unmatched_metros, no_data_metros)

    return MarketQueryResponse(
        filters=filters,
        explanation=explanation,
        unmatched_metros=unmatched_metros,
        no_data_metros=no_data_metros,
        results=results,
    )


@router.post("/feedback", status_code=204)
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> None:
    db.add(
        QueryFeedback(
            query=payload.query,
            filters=payload.filters.model_dump(mode="json"),
            rating=FeedbackRating(payload.rating),
        )
    )
    db.commit()
