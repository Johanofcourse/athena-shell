# Athena Shell

A real estate market-trend tracker for 50 US metros — home prices, rents,
income, commute times, property taxes, population, mortgage rates, and
natural hazard risk — searchable in plain English, backed entirely by
real public data.

**Live: [athenarealestate.app](https://athenarealestate.app)**

![Homepage: plain-English search bar and a geographic map of all 50 tracked metros](docs/screenshots/homepage.jpg)

![A query result: thesis-first narrative, source citation, then the supporting chart](docs/screenshots/query-result.png)

## What it does

Ask a question like "which metros have rent prices rising the fastest?"
or "why has rent been declining in Austin?" and get back a real, grounded
answer — not a model guessing at real estate facts from training data.
Every number comes from an actual public dataset; every answer is built
by running a structured query against real rows, never by letting the
model generate facts directly.

- **Trend and ranking queries** over 29 tracked metrics, with three
  ranking modes: current value, time trend, and rate of change (so
  "fastest-growing" actually ranks by rate of change, not just who's
  currently biggest).
- **"Why" questions** are answered by retrieval over real HUD market
  analysis reports (23 of 50 metros), not generated from the model's own
  assumptions.
- **Explicit about its own limits**: a question it can't answer says so
  instead of being ignored; a metro with no data for a metric says so
  instead of returning nothing; an approximated/fallback number is always
  flagged as such, never presented as the real thing.

## Data

Seven independent, real public sources — no synthetic or scraped data:

| Source | Covers |
|---|---|
| Redfin Data Center | Home sale prices, days on market, price drops, delistings/relistings |
| Apartment List | Rent estimates (by bed size), vacancy rate, time on market |
| Census ACS | Household income, commute time, property tax, population, a rent fallback for 10 metros Apartment List doesn't cover |
| Freddie Mac PMMS | 30yr/15yr fixed and 5/1 ARM mortgage rates (national) |
| BLS | Metro-level unemployment rate |
| FHFA (via FRED) | House price index |
| FEMA National Risk Index | Natural hazard risk, population-weighted from county to metro |
| HUD CHMA reports | Retrieval corpus for "why" questions (23 metros) |

Every source was independently spot-checked against known real-world
market history before being trusted, and every cross-source join has
been through at least one real, non-obvious naming mismatch along the
way — see [docs/ROADMAP.md](docs/ROADMAP.md) for the specific bugs that
turned up and how they were caught.

## How a query actually resolves

```
frontend (Vite/React)  --HTTP-->  backend (FastAPI)  --tool call-->  DeepSeek
                                        |
                                     SQLite (Metro + MarketMetric, long/tidy fact table)
```

1. The query goes to DeepSeek with two tool schemas (`query_market_metrics`
   for data questions, `search_market_commentary` for "why" questions) and
   `tool_choice: "required"` — the model must call one, but it genuinely
   decides which, and only ever returns structured arguments, validated
   with Pydantic. It never generates a market fact directly, and never
   writes SQL.
2. Those arguments run through a fixed, parameterized query path. For a
   metric question, that's a direct lookup/ranking/change-rate
   computation against real rows. For a "why" question, it's retrieval
   over the HUD corpus followed by a second, strictly-grounded model call
   that paraphrases the retrieved text — it can't introduce a claim the
   retrieved chunks don't contain.
3. The response is a thesis-first narrative, a source citation, and the
   underlying chart — in that order (an inverted-pyramid layout: the
   answer first, the supporting data last), with a transparency panel
   showing the exact resolved arguments DeepSeek produced, so the
   reasoning behind any answer is always auditable, not just trusted.

## Stack

- **Frontend**: React + TypeScript (Vite)
- **Backend**: Python (FastAPI) + SQLAlchemy + SQLite
- **NL layer**: DeepSeek (`deepseek-flash`), OpenAI-compatible tool-calling API
- **Deployment**: Oracle Cloud VM, nginx + systemd + gunicorn, real TLS, GitHub Actions CI/CD

## Testing

- **125 backend (pytest) + 38 frontend (Vitest) tests**, run on every push
  via GitHub Actions — the deterministic logic (query resolution, metro
  crosswalks, ETL, API contracts, formatting) that doesn't require a live
  model call.
- **A 47-case eval suite** (`backend/evals/`) exercises the real,
  DeepSeek-backed query resolution end to end — does the model pick the
  right metric, ranking mode, and tool for a given plain-English question.
  Kept out of CI deliberately (it costs real API usage per run) and run
  manually instead. Currently 46/47 cases, 117/118 individual checks; the
  one failure is a known, deliberately adversarial case.

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

### Running the eval suite

```bash
cd backend
python -m evals.run_eval   # uses real DeepSeek calls - small real cost
```

## Docs

- [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) — architecture, data model, API reference, env vars
- [docs/ROADMAP.md](docs/ROADMAP.md) — what's shipped and what's next, in detail
- [docs/PRODUCT_REVIEW.md](docs/PRODUCT_REVIEW.md) — an honest, warts-and-all read on where the project actually stands
