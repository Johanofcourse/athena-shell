from fastapi import APIRouter, Depends, HTTPException, Request
from openai import APIError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.nl_query import explain_filters, interpret_query, run_market_query
from app.rate_limit import limiter
from app.schemas import MarketQueryResponse, QueryRequest

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=MarketQueryResponse)
@limiter.limit("10/minute")
def run_query(request: Request, payload: QueryRequest, db: Session = Depends(get_db)) -> MarketQueryResponse:
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=503,
            detail="DEEPSEEK_API_KEY is not configured on the server.",
        )

    try:
        filters = interpret_query(payload.query)
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
