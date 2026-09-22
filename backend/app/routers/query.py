from fastapi import APIRouter, Depends, HTTPException
from openai import APIError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.nl_query import apply_filters, explain_filters, interpret_query
from app.schemas import QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def run_query(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=503,
            detail="DEEPSEEK_API_KEY is not configured on the server.",
        )

    try:
        filters = interpret_query(request.query)
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek API error: {exc}") from exc

    results = apply_filters(db, filters)
    explanation = explain_filters(filters)

    return QueryResponse(filters=filters, explanation=explanation, results=results)
