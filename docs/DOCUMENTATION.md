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
                              (Metro + MarketMetric, long/tidy fact table)
```

Two request paths through the backend:
- `GET /metros`, `GET /metros/{id}/series` - plain reads, no LLM involved.
  Used for browsing and for chart data once a metro is picked directly.
- `POST /query` - the NL path: DeepSeek resolves free text into a
  structured filter object, which then runs through the same
  parameterized query path as everything else. The model never sees or
  writes SQL.

## Data model (`backend/app/models.py`)

**`Metro`** - one row per tracked metro (50 total). Doubles as the
crosswalk between Redfin's and Apartment List's different naming
conventions for the same geography (`redfin_name`, `aptlist_name`) - see
`backend/app/market_crosswalk.py` for the full, hand-reviewed table.
`aptlist_name` is `None` for 10 metros where Redfin tracks a metropolitan
*division* (e.g. Anaheim) that Apartment List only publishes as part of a
larger combined metro (Los Angeles) - a real, deliberate gap, not a bug.

**`MarketMetric`** - one row per (metro, period, source, metric[, bed_size])
observation. A long/tidy fact table, not one wide column per metric -
adding a metric or a new source is new rows, never a schema migration.
`backend/app/ingest_market_data.py` loads all six real CSVs
(`data/samples/`) into this table; run with `python -m app.ingest_market_data`.

This replaced an earlier `Listing`/`ListingEvent` model built against a
synthetic per-listing dataset (see `git log` before this doc's current
version, or `docs/PRODUCT_REVIEW.md` for why the pivot happened). It was
removed outright once the new schema was proven working, not kept around
deprecated.

## NL query layer (`backend/app/nl_query.py`)

Design choice: **tool-calling into a fixed filter shape, not text-to-SQL.**
DeepSeek is called with a single `query_market_metrics` tool and forced to
call it (`tool_choice`). The returned arguments are parsed and validated
against `MarketQueryFilters` (Pydantic, `MetricName` is an enum - not a
free string) before touching the database.

Two query modes, both going through the same tool:
- **Trend mode** (`sort_by: "period"`, the default) - full time series for
  one or more named metros. Deliberately does **not** fall back to "all
  metros" when none are named; it says so explicitly instead (see below).
- **Ranking mode** (`sort_by: "value"`) - one point per metro at its
  latest value, sorted - for "which metro has the highest/lowest X"
  questions. `metros` is left empty to mean "all of them."

**Three honesty behaviors, deliberately built, not accidental:**
1. `unsupported_aspects` - a field on the tool schema itself. When part of
   a question can't be answered (school quality, crime, a specific
   address), the model names it here instead of silently dropping it or
   inventing a filter. This exists because early testing found the model
   would otherwise return unfiltered results with no indication part of
   the question went unanswered.
2. `no_data_metros` - a metro resolves fine but has zero rows for the
   requested metric (e.g. rent for Anaheim, which Apartment List doesn't
   cover at that granularity). Surfaced explicitly rather than returning
   an empty result silently.
3. `unmatched_metros` - a name that doesn't match any tracked metro at
   all (typo, fictional place, unsupported city). Also surfaced, not
   swallowed.

`explain_filters()` builds the human-readable explanation **from the
resolved filter object and query outcome**, not a second LLM call -
deterministic, free, and it's what actually surfaces all three behaviors
above to the user.

`run_market_query()` is the only thing that touches the database for a
query - plain SQLAlchemy `select()`s, no raw SQL, no string interpolation.

**Verified against the live API, including a real fix needed:**
`deepseek-flash` runs in "thinking" mode by default, which rejects forced
`tool_choice` outright (undocumented by DeepSeek - found by testing
directly). Fixed with `extra_body={"thinking": {"type": "disabled"}}`.

**Eval set** (`backend/evals/`): 26 cases covering every metric category,
both query modes, bed_size/time-range parsing, all three honesty
behaviors above, and (added in a second, adversarial pass) off-topic
input, a prompt-injection attempt, a typo, a self-contradictory ranking
question, weird casing, and a relative time range - plus a repeatability
check that re-runs one ambiguous ranking query 5 times and reports whether
the chosen metric stays consistent. Run with `python -m evals.run_eval`
(costs a small amount of real DeepSeek usage). Current result: 26/26
cases, 59/59 individual checks, 5/5 repeatability.

Read that carefully, not proudly. It means these 26 attempts (including
ones written specifically to break it) didn't find a failure - that's
weaker evidence than it sounds, since everything passing on the first
adversarial attempt is at least as consistent with "the cases weren't hard
enough" as with "the system is robust." Two specific nuances: the typo
case likely passes because DeepSeek normalizes the input before our
metro-matcher (plain substring matching, not fuzzy) ever sees it - real
robustness, but from the LLM layer, not this codebase; and the
repeatability check coming back stable does not contradict the
metric-choice variance observed earlier by hand (two separate manual
tests picked different metrics for the same ranking question) - 5 samples
simply didn't reproduce it. A perfect score is a reason to write harder
cases, not a finish line.

### Guardrails / abuse prevention

The realistic abuse case for an open `/query` endpoint backed by a paid
LLM call isn't "someone tricks it into writing a PDF" - forced
`tool_choice` already makes that structurally impossible, since the model
can only ever return `query_market_metrics` arguments, never free text,
and nothing it writes reaches the client directly. The real risk is
someone hammering the endpoint to run up the API bill. Mitigated by:

- `QueryRequest.query` is capped at 300 characters (Pydantic
  `max_length`) - rejects oversized payloads before they reach the model.
- `POST /query` is rate-limited to 10 requests/minute per client IP
  (`slowapi`, in-memory) - verified locally: request 11 in a burst
  returns `429`. This guards against rapid-fire abuse, not overall usage.
- **Free-tier daily quota** (`backend/app/usage.py`, `QueryUsage` table):
  10 queries per IP per UTC calendar day, persisted in the database (not
  in-memory, so it survives a restart unlike the burst limiter above).
  Checked *before* the DeepSeek call, so a rejected request never costs
  anything. Returns 429 with an honest message - "you've used today's
  free 10 queries, resets tomorrow" - deliberately with no mention of a
  subscription, since none exists yet. This table is meant to be the
  foundation Phase 7 (real accounts/payments) builds tier enforcement on
  top of later, not a throwaway stopgap. Verified against the real
  endpoint at the boundary: the 10th call succeeds, the 11th returns 429
  without reaching DeepSeek.
  **Loopback (127.0.0.1/::1) is exempt outright** - needed for local
  dev/testing, verified for both address forms directly and through the
  real endpoint. Safe for local development; if a reverse proxy is ever
  added in front of this (Phase 5), the IP extraction and this exemption
  both need revisiting together, since a misconfigured proxy could make
  every real request look like it's coming from loopback.

Known limits: in-memory rate limiting (the burst limiter, not the daily
quota) doesn't scale across multiple backend instances - fine for a
single-instance deployment, would need a shared store (Redis) if this
ever runs horizontally scaled. The daily quota keys on IP alone, which
over- or under-counts for shared/NAT'd or VPN'd connections - an accepted
approximation until real accounts exist. There's also still no auth, and
no server-side spend cap on the DeepSeek key itself - that has to be set
directly in DeepSeek's dashboard, it isn't something the app can enforce
from the outside.

## Frontend (`frontend/src/`)

**Visual design**: the industrial/hazard-signage direction from
`PREFERENCES.md` (Phase 2) - dark, high-contrast, stencil display type
(Big Shoulders Stencil Display), monospace data readouts (IBM Plex Mono),
sharp corners, a hazard-stripe accent bar. One deliberate identity, not a
theme that softens for `prefers-color-scheme: light`.

**Value formatting** (`format.ts`): metrics aren't all the same *kind* of
number - `median_sale_price`/`median_rent`/`median_price_per_sqft` are
currency, `vacancy_rate` is a 0-1 fraction needing percent conversion,
`price_drop_pct_avg` and similar are already percent numbers needing only
a `%` suffix, and everything else (counts, days) is a plain comma-grouped
number. `formatMetricValue(metric, value)` picks the right one - applying
`$` formatting to a percentage or a day-count would be wrong, not just
inconsistent, so this is metric-aware rather than a single blanket
formatter.

**Result analysis** (`analysis.ts`): a plain-language summary line
(`summarizeResults()`) computed directly from the returned data points -
first/last value, percent change, peak/trough with date for trend mode;
leader/laggard for ranking mode. Same reasoning as `explain_filters()` on
the backend: deterministic and derived from the real numbers, not a
second LLM call, so it can never claim something the data doesn't back up.

## API reference

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/metros` | All tracked metros, with sale/rent data availability flags |
| GET | `/metros/{id}/series?metric=&bed_size=` | Raw time series for one metro/metric, for direct charting |
| POST | `/query` | `{"query": "<natural language>"}` -> `{filters, explanation, unmatched_metros, no_data_metros, results}` |

Full request/response schemas: `backend/app/schemas.py`, or run the backend
and check `/docs` (FastAPI's auto-generated Swagger UI).

## Environment variables

**Backend** (`backend/.env`, see `.env.example`):

| Var | Purpose |
|---|---|
| `DEEPSEEK_API_KEY` | Required for `/query`; missing key returns a 503 |
| `DEEPSEEK_BASE_URL` | Default `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | Default `deepseek-flash` |
| `DATABASE_URL` | Default `sqlite:///./athena.db` |
| `CORS_ORIGINS` | Comma-separated allowed origins |

**Frontend** (`frontend/.env`, see `.env.example`):

| Var | Purpose |
|---|---|
| `VITE_API_URL` | Backend base URL, default `http://localhost:8000` |

## Setting up a fresh database

```bash
cd backend
python -m app.ingest_market_data   # loads data/samples/*.csv into athena.db
```

There's no synthetic-data seed script anymore - real data replaced it.

## Current limitations

- No automated test suite (backend or frontend) - the eval set tests the
  NL layer specifically, not general code correctness.
- No auth - every endpoint is open. Fine for a local portfolio demo, not
  for anything deployed publicly as-is.
- No deployment/CI pipeline configured yet.
- Census ACS not yet integrated (pending API key) - would add an
  independent benchmark on top of Redfin/Apartment List, see
  `ROADMAP.md` Phase 3.
