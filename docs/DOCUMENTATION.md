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
crosswalk between Redfin's, Apartment List's, and Census's different
naming conventions for the same geography (`redfin_name`, `aptlist_name`,
`census_income_name`) - see `backend/app/market_crosswalk.py` for the
full, hand-reviewed table. `aptlist_name` and `census_income_name` are
both `None` for the *same* 10 metros, where Redfin tracks a metropolitan
*division* (e.g. Anaheim) that Apartment List and Census's metro-level
income table only publish as part of a larger combined metro (Los
Angeles) - a real, deliberate gap, not a bug. (Census's own naming also
drifts across time within a single source - e.g. Denver is
"Denver-Aurora-Lakewood, CO" in Apartment List's crosswalk entry but
"Denver-Aurora-Centennial, CO" in Census's 2024 data - which is why this
is a hand-reviewed table, not a live string match.)

**`MarketMetric`** - one row per (metro, period, source, metric[, bed_size])
observation. A long/tidy fact table, not one wide column per metric -
adding a metric or a new source is new rows, never a schema migration.
Census rows (`median_household_income`, `median_gross_rent`) are a single
snapshot per metro (ACS 5-Year 2024) rather than a monthly series - the
fact table handles a one-point "series" the same way it handles a
176-point one. `backend/app/ingest_market_data.py` loads all real CSVs
(`data/samples/`) into this table; run with `python -m app.ingest_market_data`.

**`NationalMetric`** - one row per (period, source, metric), deliberately
*not* `MarketMetric` with a fake "United States" `Metro` row. Genuinely
national series (currently: Freddie Mac's PMMS mortgage rates) aren't a
per-metro fact, and forcing one into the metro crosswalk would show up
oddly in the metro browsing grid and make its honesty-flag columns
meaningless. `period` is the real reported date (weekly for PMMS), not
bucketed to first-of-month - there's no per-metro dimension to justify
throwing away real granularity. Loaded by
`backend/app/ingest_national_data.py`, called from
`ingest_market_data.ingest()` so a fresh setup is still one command.

**BLS unemployment rate** is a normal per-metro `MarketMetric` (metric
`unemployment_rate`, source `BLS`) - unlike mortgage rates, it's a real
per-metro fact, so it doesn't need `NationalMetric`. What's different is
the crosswalk and the ingest path: `BLS_AREA_CODES`
(`market_crosswalk.py`) is a plain `{metro_id: area_code}` dict, not a
7th crosswalk column, since it's used to construct BLS API series IDs
(`"LAU" + area_code + measure_code`) rather than matched against a
downloaded file's column headers. And unlike every other source, the
data comes from a live, registered API call
(`backend/app/fetch_bls_unemployment.py`, run manually/occasionally, not
part of the regular ingest), whose raw JSON response is saved to
`data/samples/bls_unemployment_rate.json` so the actual ingest step
(`ingest_bls_unemployment()` in `ingest_market_data.py`) stays offline
and deterministic like everything else. Real find: BLS's LAUS covers
metropolitan *divisions* separately, so the same 10 metros missing
`aptlist_name`/`census_income_name` still get **real, non-approximated**
unemployment data here - not another gap or fallback.

**FHFA house price index** (metric `house_price_index`, source `FRED`)
follows the same pattern as BLS unemployment - `FHFA_HPI_SERIES_IDS`
(`market_crosswalk.py`), a live API fetch
(`backend/app/fetch_fred_house_price_index.py`, saved to
`data/samples/fred_house_price_index.json`), and an offline
`ingest_fhfa_hpi()`. The coverage gap is real and meaningfully different
from every other source, though: FHFA doesn't publish one combined index
for large multi-division metros at all (Los Angeles, Chicago, San
Francisco, Seattle, Washington DC, Miami, Philadelphia, Dallas, Detroit),
and three of the usual 10 metro-division gap metros have no current
division series either - 38/50 real matches, not 50/50 like BLS. Using
one division's number to stand in for a combined metro's would have been
the exact mistake this project has refused to make elsewhere, so those
12 are genuine `no_data_metros` gaps - no new honesty mechanism needed,
the existing one already covers it.

**`METRO_COORDINATES`** (`market_crosswalk.py`) isn't tied to any
source's own data-availability convention the way the dicts above are -
it's real lat/long for map-plotting, sourced from the Census Bureau's own
Gazetteer files (CBSA centroids for the 40 combined metros, the actual
named city's point from the Place gazetteer for the 10 metro-division
metros). The one crosswalk in this project with zero gaps. Exposed via
`GET /metros`'s `latitude`/`longitude` fields, consumed by
`UsMetroMap.tsx`.

This replaced an earlier `Listing`/`ListingEvent` model built against a
synthetic per-listing dataset (see `git log` before this doc's current
version, or `docs/PRODUCT_REVIEW.md` for why the pivot happened). It was
removed outright once the new schema was proven working, not kept around
deprecated.

**`MarketCommentaryChunk`** - Phase 8's table, one row per page of a HUD
Comprehensive Housing Market Analysis (CHMA) PDF, for the
`search_market_commentary` tool (see below). `HUD_CHMA_FILES`
(`market_crosswalk.py`) maps `metro_id` to a filename - a real, honest
subset of the 50 metros (23 as of this writing), hand-curated the same
way as every other bot-gated source here: HUD's state listing pages
don't respond to automated fetches, so coverage was checked and reports
downloaded by hand, not scraped. `as_of_date` is the report's own stated
date, extracted from its text, not inferred from a filename or treated as
"current" just because it's the newest one HUD has published - two
metros in the set are flagged exceptions for exactly this reason:
`los-angeles-ca` only has a 2013 full-metro report (newer ones exist but
only cover part of the metro), and `providence-ri` is a statewide report,
not a metro-specific one. The PDFs themselves are **not in git** - see
`.gitignore` and this doc's Deployment section.

## NL query layer (`backend/app/nl_query.py`, `backend/app/market_commentary.py`)

Design choice: **tool-calling into a fixed filter shape, not text-to-SQL.**
DeepSeek is given two tools and `tool_choice="required"` - it must call
one of them, but genuinely picks which: `query_market_metrics` for "what"
questions (an exact number, a trend, a ranking), or `search_market_commentary`
(Phase 8) for "why" questions about one named metro, answered from a real,
cited HUD report excerpt instead of the structured database. `interpret_query`
returns a `MarketQueryFilters` or a `CommentaryQuery` depending on which
the model called, and `routers/query.py` branches on `isinstance()` -
the two response shapes are never blended (see `MarketQueryResponse`:
`filters`/`results` for the metrics path, `commentary` for the other,
whichever one wasn't used stays empty/`None`). The returned arguments are
parsed and validated against `MarketQueryFilters` or `CommentaryQuery`
(Pydantic) before touching the database.

**`search_market_commentary`** (`market_commentary.py`): given a metro
and a short topic phrase, looks up that metro's `MarketCommentaryChunk`
rows and ranks them by TF-IDF similarity to the topic - computed
in-process, fresh, over just that one metro's handful of chunks, not a
precomputed vector index. This is deliberately not semantic/embedding
search: metro selection already narrows retrieval to one ~30-page
document before ranking ever runs, so the real problem is "which section
of this one report," not open-domain search - more infrastructure than
that problem needs. Two honesty-flag outcomes, same pattern as the
metrics path: an unresolved metro name is `unmatched_metros`; a resolved
metro with zero HUD coverage (not in the hand-curated `HUD_CHMA_FILES`
set) is `no_data_metros` - never silently empty, never a different
metro's report substituted in.

The retrieved chunks are raw PDF text, extracted one page at a time -
some start mid-sentence or carry a "## " heading marker, artifacts of
chunking rather than content. Rather than show that directly as the
answer, `synthesize_commentary_answer` makes a second DeepSeek call that
turns those chunks into a real, thesis-first answer to the person's
actual question (one direct sentence, then supporting detail, in the
model's own words) - grounded strictly in the chunks it's handed, told
explicitly not to go beyond them. This becomes `MarketQueryResponse.
explanation` for a commentary response; the raw chunks still render
below it in `commentary.chunks`, so the paraphrase can always be checked
against the real source. If that second call itself fails, `routers/
query.py` falls back to `explain_commentary`'s deterministic "Showing
HUD market commentary for..." sentence rather than failing the whole
request - the same call-then-fallback pattern `interpret_query`'s own
caller already uses. Like `interpret_query`'s tool-choice behavior, this
is a live model call with no unit test around its actual output quality -
covered by manual verification and the eval suite, not pytest.

Two query modes, both going through the same tool:
- **Trend mode** (`sort_by: "period"`, the default) - full time series for
  one or more named metros. Deliberately does **not** fall back to "all
  metros" when none are named; it says so explicitly instead (see below).
- **Ranking mode** (`sort_by: "value"`) - one point per metro at its
  latest value, sorted - for "which metro has the highest/lowest X"
  questions. `metros` is left empty to mean "all of them."

A third category, **national metrics** (mortgage rates), has no metro
dimension at all. `_sanitize_filters` clears `metros` for these
deterministically regardless of what the model produced (same guardrail
pattern as `bed_size`), and `run_market_query` routes them to
`_run_national_query`, which queries `NationalMetric` directly - trend
mode returns the full series, ranking mode returns the single latest
point, and results are labeled `"United States"` to fit the existing
`MarketMetricPoint` shape without a schema change.

**Four honesty behaviors, deliberately built, not accidental:**
1. `unsupported_aspects` - a field on the tool schema itself. When part of
   a question can't be answered (school quality, crime, a specific
   address), the model names it here instead of silently dropping it or
   inventing a filter. This exists because early testing found the model
   would otherwise return unfiltered results with no indication part of
   the question went unanswered.
2. `no_data_metros` - a metro resolves fine but has zero rows for the
   requested metric (e.g. household income for Anaheim, which Census's
   metro-level table doesn't cover at that granularity, and no
   county-level fallback was pulled for). Surfaced explicitly rather than
   returning an empty result silently.
3. `unmatched_metros` - a name that doesn't match any tracked metro at
   all (typo, fictional place, unsupported city). Also surfaced, not
   swallowed.
4. `approximated_metros` - a `median_rent` (or `rent_to_income_pct`)
   request was answered using Census's county-level `median_gross_rent`
   instead of real Apartment List data, for the same 10 metro-division
   metros above (e.g. Anaheim). A real number from a different, coarser
   survey - always flagged, never silently presented as if it were the
   same measure. Only offered when the question wasn't bedroom-specific
   (Census doesn't split gross rent by bed size); a 1BR/2BR-specific
   question for one of these metros still comes back as genuine
   `no_data_metros`. See `run_market_query()`'s `_fetch_rent_rows()`.

`explain_filters()` builds the human-readable explanation **from the
resolved filter object and query outcome**, not a second LLM call -
deterministic, free, and it's what actually surfaces all three behaviors
above to the user.

`run_market_query()` is the only thing that touches the database for a
query - plain SQLAlchemy `select()`s, no raw SQL, no string interpolation.

**`rent_to_income_pct`** (computed, not a directly ingested metric):
`(median rent x 12) / median household income x 100`. Income is a single
ACS snapshot, held constant across whatever rent periods exist, so a
trend query for this metric shows real month-to-month rent movement
against a fixed income baseline - a real combination of two real numbers,
not a fabricated series. `median_gross_rent` (the Census fallback above)
is deliberately **excluded** from `query_market_metrics`'s `metric` enum
(`SELECTABLE_METRICS` in `nl_query.py`) - it's never something a user
picks directly, only an internal substitution `run_market_query()` makes
for `median_rent` requests.

**Verified against the live API, including a real fix needed:**
`deepseek-flash` runs in "thinking" mode by default, which rejects forced
`tool_choice` outright (undocumented by DeepSeek - found by testing
directly). Fixed with `extra_body={"thinking": {"type": "disabled"}}`.

**Eval set** (`backend/evals/`): 37 cases covering every metric category
(including the Census-backed `median_household_income`, the computed
`rent_to_income_pct`, the national `mortgage_rate_*` series, BLS
`unemployment_rate`, and FHFA `house_price_index`), both query modes,
bed_size/time-range parsing, all four honesty behaviors above (including
the `median_rent` -> `median_gross_rent` fallback and the genuine income
gap it doesn't paper over), an adversarial pass (off-topic input, a
prompt-injection attempt, a typo, a self-contradictory ranking question,
weird casing, a relative time range), and a permanent regression case -
plus a repeatability check that re-runs one ambiguous ranking query 5
times and reports whether the chosen metric stays consistent. Run with
`python -m evals.run_eval` (costs a small amount of real DeepSeek usage).
Current result: **37/37 cases, 88/88 individual checks**; the
repeatability check came back stable this
run (5/5 same metric) - consistent with the known non-determinism being
real but intermittent, not something a code fix should be expected to
eliminate outright (see `PRODUCT_REVIEW.md`).

Read that carefully, not proudly. A clean run means these attempts
(including ones written specifically to break it) didn't find a failure -
that's weaker evidence than it sounds, since everything passing on the
first adversarial attempt is at least as consistent with "the cases
weren't hard enough" as with "the system is robust." Two specific
nuances: the typo case likely passes because DeepSeek normalizes the
input before our metro-matcher (plain substring matching, not fuzzy) ever
sees it - real robustness, but from the LLM layer, not this codebase; and
the repeatability check reproducing non-determinism on one run and not
another (5/5 stable, then 2 different metrics across 5 runs, now 2 again)
is itself the finding - it's genuinely inconsistent, not flaky
measurement. A perfect score is a reason to write harder cases, not a
finish line.

### Multi-turn conversation

There's no server-side session store - the client holds conversation
state and resends it. `QueryRequest.history` is a list of up to 5 prior
`{query, filters}` turns (`ConversationTurn`). `interpret_query()` replays
each one as a real `user` message, a synthetic `assistant` message
carrying the tool_call `filters` as its arguments, and a `tool` message
acknowledging it - OpenAI-compatible chat format requires that shape
(a tool_calls message must be followed by a matching tool message before
the next turn). This isn't a paraphrase of history fed to the model as
text; it's the same structure a real multi-turn tool-calling conversation
would have.

Verified against the live API: a follow-up ("what about Denver?") that
depends entirely on prior context correctly carries the metric forward
and swaps the metro; a later follow-up in the same conversation correctly
overrides the metric while keeping the metro - so it's using context, not
just repeating the first answer.

**Real bug found while verifying this, not before:** `bed_size` (only
meaningful for `median_rent`) could carry over from a rent question into
a follow-up about an unrelated metric. Every non-rent metric is stored
with `bed_size=NULL`, so filtering on a stale `"overall"` value silently
returned zero rows - the `no_data_metros` honesty path firing for the
wrong reason (a real bug dressed as correct behavior). Fixed with
`_sanitize_filters()` in `nl_query.py`: a deterministic post-processing
step that clears `bed_size` whenever the metric isn't `median_rent`,
regardless of what the model produced. A prompt-wording fix was
considered and rejected - it wouldn't guarantee the behavior the way a
code-level check does. Added as a permanent case in the eval set
(`regression_stale_bed_size_across_metric_switch`) so it can't silently
regress.

### Transparency panel and feedback loop (`frontend/src/components/`)

`InterpretationPanel` renders the exact `MarketQueryFilters` object
returned by `/query` - not a paraphrase, the real resolved arguments.
The API already returned this; the panel is where it becomes visible
instead of just being true in principle.

`FeedbackWidget` posts `{query, filters, rating}` to `POST
/query/feedback`, stored in `QueryFeedback` (query text + filters as JSON
+ rating + timestamp). No admin UI yet - review it with a direct query
against the table. This is meant to be the raw material for growing the
eval set from real usage over time, not just hand-written cases.

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

**Visual design**: the industrial direction from `PREFERENCES.md` (Phase
2) - dark, high-contrast, stencil display type (Big Shoulders Stencil
Display), monospace data readouts (IBM Plex Mono), sharp corners, a
diagonal accent bar. Re-colored blue/red (from the original hazard-
yellow/black) after real viewer feedback that the original read as
construction-site caution tape - same bones, different tokens (`--accent`,
`--danger` in `index.css`). One deliberate identity either way, not a
theme that softens for `prefers-color-scheme: light`.

**Metro browsing map** (`UsMetroMap.tsx`): an accurate US map
(`react-simple-maps` + `d3-geo`, rendering `us-atlas`'s real Census
TIGER/Line-derived state topology via `geoAlbersUsa`) with all 50 metros
plotted as clickable markers, plus a synced list alongside - not an
illustrated/isometric map, since that style is normally hand-drawn art,
not something derivable from coordinate data. Coordinates come from
`METRO_COORDINATES` (`market_crosswalk.py`), the one crosswalk in this
project with zero gaps (see below). Uses `us-atlas`'s raw (non-Albers-
pre-projected) topology specifically, so both the state outlines and the
markers get projected through the same `geoAlbersUsa` call - the
pre-projected variant would silently misalign the two.

**Value formatting** (`format.ts`): metrics aren't all the same *kind* of
number - `median_sale_price`/`median_rent`/`median_price_per_sqft`/
`median_household_income`/`median_gross_rent` are currency, `vacancy_rate`
is a 0-1 fraction needing percent conversion, `price_drop_pct_avg`,
`rent_to_income_pct`, and similar are already percent numbers needing
only a `%` suffix, and everything else (counts, days) is a plain
comma-grouped number. `formatMetricValue(metric, value)` picks the right
one - applying `$` formatting to a percentage or a day-count would be
wrong, not just inconsistent, so this is metric-aware rather than a
single blanket formatter.

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
| GET | `/metros` | All tracked metros, with sale/rent/income data availability flags |
| GET | `/metros/{id}/series?metric=&bed_size=` | Raw time series for one metro/metric, for direct charting. `median_rent` goes through the same Census gross-rent fallback as `/query` below. |
| POST | `/query` | `{"query": "<natural language>", "history": [{"query", "filters"}, ...]}` -> `{filters, explanation, unmatched_metros, no_data_metros, approximated_metros, results, commentary}`. `history` is optional, max 5 turns. Exactly one of `results`/`commentary` is populated depending on which tool the model called - `filters` is `null` for a commentary response (see NL query layer above). History replay only carries `query_market_metrics` turns forward - a commentary turn isn't resent as conversation state (Phase 8, a known scope limit, not a bug). |
| POST | `/query/feedback` | `{"query", "filters", "rating": "up"\|"down"}` -> 204. Logged to `QueryFeedback` for eval growth. |

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
| `EXEMPT_IPS` | Comma-separated IPs exempt from the free daily query cap (`app/usage.py`), beyond loopback. Set directly on the server, never committed - a real IP is identifying info. |

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

HUD CHMA commentary (Phase 8) is optional and ingests separately from
everything else: if `data/samples/hud_chma/` is empty or missing, the
ingest run prints a per-metro skip message and continues normally -
`search_market_commentary` just has nothing to find until the PDFs are
in place. They're not in git (see Deployment below), so a fresh clone
genuinely won't have this corpus until someone copies it in by hand.

## Testing

Two distinct layers, deliberately not merged into one suite:

- **`backend/tests/`** (pytest, `cd backend && pytest`) - general code
  correctness: the deterministic parts of `nl_query.py` (the median_rent
  fallback, `rent_to_income_pct` math, `explain_filters`' text),
  structural invariants on `market_crosswalk.py`, the ETL functions in
  `ingest_market_data.py` against tiny fixture CSVs, and API contract
  tests via FastAPI's `TestClient`. Everything runs against a synthetic
  fixture database (fake metros - Testville, Gapford, Emptyburg - never
  the real `athena.db`), takes well under a second, and needs no
  DeepSeek key. `POST /query` itself is out of scope here - it needs a
  live LLM call, which is what the eval suite is for.
- **`frontend/` tests** (Vitest + React Testing Library,
  `cd frontend && npm run test`) - `format.ts` and `analysis.ts` as pure
  functions, plus component tests for `MetroGrid`, `InterpretationPanel`,
  and `QueryResults`' empty-state path. Chart rendering (Recharts) is
  intentionally left to real-browser verification (Playwright) rather
  than jsdom, which doesn't implement the layout/`ResizeObserver`
  behavior Recharts needs to size itself.
- **`backend/evals/`** (the NL-layer eval suite) is a third, separate
  thing - see the NL query layer section above. It costs real DeepSeek
  API usage per run, so it's run manually (about twice a week) rather
  than wired into CI.

**CI** (`.github/workflows/ci.yml`): the pytest and Vitest suites plus
`tsc -b` run on every push to `main` and every PR - all free, no live
keys required. The eval suite is deliberately excluded from CI for the
cost reason above.

## Deployment

Live at `https://athenarealestate.app` (frontend) and
`https://api.athenarealestate.app` (backend), on a second Oracle Cloud
Always Free VM, separate from Apollo Shell's (same VCN, within the same
free-tier budget split). Oracle Linux 9.

- **Backend**: gunicorn with `uvicorn.workers.UvicornWorker`, run as a
  systemd service (`athena-backend.service`) - `Restart=always`, enabled
  on boot, logs to the systemd journal. nginx reverse-proxies
  `api.athenarealestate.app` to it on `127.0.0.1:8001`.
- **Frontend**: a static `vite build` output, served directly by nginx
  from `/var/www/athenarealestate` - no Python process involved, same as
  the plan from the start.
- **TLS**: Certbot/Let's Encrypt certificates for the root domain, `www`,
  and the `api` subdomain, auto-renewing; nginx redirects HTTP to HTTPS.
- **Proxy headers**: the backend trusts `X-Forwarded-For` from
  `127.0.0.1` only
  (`uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware`, wired in
  `app/main.py` as a separate `asgi_app` export - gunicorn serves
  `app.main:asgi_app`, not `app.main:app`, in production). Without this,
  the rate limiter would see every visitor as the same client, since
  `request.client.host` is otherwise always nginx's own address.
- **Secrets**: `.env` and the already-ingested `athena.db` were copied to
  the server via `scp`, never through git.
- **HUD CHMA PDFs** (Phase 8, `data/samples/hud_chma/`): same `scp`
  treatment as the secrets above, for the same reason - real downloaded
  source data, not code, deliberately kept out of git for its size (83MB
  and growing). A deployed environment needs this folder copied by hand
  before `search_market_commentary` has anything to find; it's not pulled
  by `git pull` the way everything else here is.
- **Deploys**: `.github/workflows/deploy.yml`, manual `workflow_dispatch`
  trigger only - a human clicks "Run workflow" in the Actions tab, same
  pattern as Apollo Shell's deploy.yml, deliberately decoupled from
  merging a PR (merging never touches the VM by itself). SSHes in, pulls
  `main`, reinstalls backend deps, **re-runs the test suite on the server
  itself** (not just trusting the earlier CI run), rebuilds the frontend
  (Node 22, installed on the VM for this), redeploys
  `/var/www/athenarealestate`, restarts `athena-backend`, then verifies
  by curling the backend's local health check *and* the real public
  `athenarealestate.app`/`api.athenarealestate.app` URLs - if anything
  fails, the run stops and shows red in the Actions tab instead of
  silently leaving a half-deployed state. The HUD CHMA PDFs still need a
  one-time manual `scp` per environment (see above) - the deploy workflow
  doesn't copy them, since they're not in git for it to pull.

## Current limitations

- No auth - every endpoint is open to the public internet now that this
  is deployed. Acceptable for a demo someone is deliberately pointed to,
  not for anything that needs real access control.
- No CD pipeline yet - deploys are manual SSH, not automated on merge
  (CI exists; CD doesn't - see `ROADMAP.md` Phase 5).
- Census `S0801` (commute time) not pulled - the `api.census.gov` API key
  signup issue is unresolved, and this wasn't pursued further via manual
  table-browser downloads this round. See `ROADMAP.md` Phase 3.
