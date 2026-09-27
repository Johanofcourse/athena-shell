# Athena Shell

A real estate market-trend tracker — home prices, rents, days-on-market,
price drops, and relisting patterns across 50 US metros since 2012/2017,
with a natural-language query layer over the data and a React/TypeScript
frontend.

## Stack

- **Frontend**: React + TypeScript (Vite)
- **Backend**: Python (FastAPI) + SQLAlchemy + SQLite
- **NL query layer**: DeepSeek (`deepseek-flash`) via its OpenAI-compatible API, using tool-calling to resolve a query into a structured, safe filter object — never raw SQL generation.
- **Data**: real historical market data - Redfin Data Center (home sales) + Apartment List (rentals) - not synthetic.

## Architecture

```
frontend (Vite/React)  --HTTP-->  backend (FastAPI)  --tool call-->  DeepSeek
                                        |
                                     SQLite (Metro + MarketMetric, long/tidy fact table)
```

`Metro` (50 tracked metros) and `MarketMetric` (one row per metro/period/metric) hold the real Redfin + Apartment List data, loaded by `python -m app.ingest_market_data`.

A natural-language query is resolved in two steps:
1. DeepSeek is called with a `query_market_metrics` tool schema and forced to call it — it only ever returns structured filter arguments, which are validated with Pydantic.
2. Those filters run through a fixed, parameterized SQLAlchemy query path. The model never touches the database directly.

The NL layer also has to be honest about its limits: it names parts of a question it can't answer instead of ignoring them, and says explicitly when a metro has no data for a requested metric rather than returning nothing silently. See [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) for why that mattered enough to build deliberately.

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your DEEPSEEK_API_KEY
python -m app.ingest_market_data   # loads the real data (athena.db)
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000` (docs at `/docs`).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App runs at `http://localhost:5173`.

### Running the eval set

```bash
cd backend
python -m evals.run_eval   # uses real DeepSeek calls - small real cost
```

## Docs

- [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) — architecture, data model, API reference, env vars
- [docs/ROADMAP.md](docs/ROADMAP.md) — what's next, in priority order
- [docs/PRODUCT_REVIEW.md](docs/PRODUCT_REVIEW.md) — honest read on where the project actually stands
