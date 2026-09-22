# Documentation

Technical reference for how Athena Shell is built. For setup commands, see
the [root README](../README.md). For where the project is headed, see
[ROADMAP.md](ROADMAP.md).

## Architecture

```
frontend (Vite/React/TS)  --HTTP-->  backend (FastAPI)  --tool call-->  DeepSeek
        :5173                              :8000
                                             |
                                          SQLite
                                (listings + event timeline)
```

Two request paths through the backend:
- `GET /listings`, `GET /listings/{id}` - plain reads, no LLM involved.
- `POST /query` - the NL path: DeepSeek resolves free text into a structured
  filter object, which then runs through the same parameterized query path
  as everything else. The model never sees or writes SQL.

## Data model (`backend/app/models.py`)

**`Listing`** - one row per property. Carries both raw facts (address,
beds/baths, sqft) and a set of *denormalized summary fields* derived from
that listing's event history: `current_price`, `price_drop_amount`,
`price_drop_pct`, `days_on_market`, `total_days_on_market`,
`relist_count`, `status`. These exist so the query layer can filter/sort
without recomputing history on every request. They're computed once, at
write time (currently only in `seed.py`) - if a real ingestion pipeline
ever replaces the seed script, it owns keeping these fields correct.

**`ListingEvent`** - append-only. One row per state change:
`listed` / `price_change` / `status_change` / `relisted` / `delisted` /
`sold`. This is the source of truth for a listing's history; the detail
view (`GET /listings/{id}`) returns the full ordered list.

## NL query layer (`backend/app/nl_query.py`)

Design choice: **tool-calling into a fixed filter shape, not text-to-SQL.**
DeepSeek is called with a single `filter_listings` tool and forced to call
it (`tool_choice`). The returned arguments are parsed and validated against
`QueryFilters` (Pydantic) before touching the database. This trades some
query flexibility for safety and testability - malformed or adversarial
input fails Pydantic validation instead of reaching SQL.

`explain_filters()` builds the human-readable "Showing listings..." summary
**from the resolved filter object**, not a second LLM call - deterministic,
free, and can't say something different from what actually ran.

`apply_filters()` is the only thing that touches the database for a query -
a plain SQLAlchemy `select()` with `.where()` clauses added conditionally
per filter field.

This layer is currently **unverified against the live DeepSeek API** - see
`ROADMAP.md` Phase 1 and `PRODUCT_REVIEW.md`.

## API reference

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/listings?limit=` | Recent listings, newest activity first |
| GET | `/listings/{id}` | One listing with full event history |
| POST | `/query` | `{"query": "<natural language>"}` -> `{filters, explanation, results}` |

Full request/response schemas: `backend/app/schemas.py`, or run the backend
and check `/docs` (FastAPI's auto-generated Swagger UI).

## Environment variables

**Backend** (`backend/.env`, see `.env.example`):

| Var | Purpose |
|---|---|
| `DEEPSEEK_API_KEY` | Required for `/query`; missing key returns a 503 |
| `DEEPSEEK_BASE_URL` | Default `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | Default `deepseek-chat` |
| `DATABASE_URL` | Default `sqlite:///./athena.db` |
| `CORS_ORIGINS` | Comma-separated allowed origins |

**Frontend** (`frontend/.env`, see `.env.example`):

| Var | Purpose |
|---|---|
| `VITE_API_URL` | Backend base URL, default `http://localhost:8000` |

## Current limitations

- No automated test suite (backend or frontend).
- Synthetic data only (`backend/app/seed.py`); no real listings source.
- No auth - every endpoint is open. Fine for a local portfolio demo, not
  for anything deployed publicly as-is.
- No deployment/CI pipeline configured yet.
