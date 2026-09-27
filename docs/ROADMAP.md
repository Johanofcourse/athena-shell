# Roadmap

Athena Shell has two goals that both need to hold up: a genuinely useful
market-trend tool, and a portfolio piece that demonstrates forward-deployed
AI engineering skill. Phases below are ordered by what actually derisks
those goals, not by what's easiest to build next.

## Phase 0 — Scaffold (done, PR #1)
Originally built against a synthetic per-listing dataset (`Listing` +
`ListingEvent`, a seed script generating 180 fake listings). That model
and its seed script were **removed outright** once Phase 3's real-data
schema was proven working - not deprecated, not kept around. See Phase 3.
- [x] REST API, NL query layer wired to DeepSeek, React/TS UI - all since
      rebuilt against real data (Phase 3), described there.

## Phase 1 — Prove the NL layer works (done)
The differentiating part of this project, and the thing most likely to be
probed hardest in an interview.
- [x] Guardrails ahead of a live key: `/query` input capped at 300 chars,
      rate-limited to 10 req/min/IP (verified locally - burst of 11
      returns `429`). Still open: no auth, no spend cap on the DeepSeek
      key itself (must be set in DeepSeek's own dashboard). See
      `DOCUMENTATION.md` -> Guardrails.
- [x] Wire a real `DEEPSEEK_API_KEY` and run `/query` end to end. Two real
      fixes needed, not a clean first try: a stale model name
      (`deepseek-chat` -> `deepseek-flash`), and `deepseek-flash`'s
      default "thinking" mode rejecting forced `tool_choice` outright (400,
      undocumented by DeepSeek - found by testing directly against the
      API, fixed with `extra_body={"thinking": {"type": "disabled"}}`).
- [x] **Honesty fix, not just noted:** early manual testing found "houses
      near good schools" didn't hallucinate a filter but silently dropped
      that part of the question. Fixed by giving the tool schema an
      `unsupported_aspects` field the model populates instead of ignoring
      or inventing - surfaced in `explain_filters()`. Same pattern applied
      to two more real cases found during the Phase 3 rebuild: a metro
      that resolves but has no data for the requested metric
      (`no_data_metros`), and a metro name that doesn't match anything
      tracked at all (`unmatched_metros`).
- [x] Build a real eval set: 18 cases in `backend/evals/`, covering every
      metric category, both query modes (trend/ranking), and all three
      honesty behaviors above. Run with `python -m evals.run_eval`.
      Current result: **18/18 cases, 44/44 checks** - read carefully in
      `DOCUMENTATION.md`, not as a finish line. It means the eval hasn't
      found a failure yet; it doesn't mean there isn't one. Known gaps:
      no adversarial-input cases, doesn't probe the metric-choice
      non-determinism observed by hand (same ranking question picked a
      different, still-defensible metric on different runs).

## Phase 2 — Visual redesign
- [ ] Replace the current generic/flat UI with the industrial,
      hazard-signage-inspired direction from `PREFERENCES.md`. Not started
      - deliberately deprioritized behind proving the data/AI layer, per
      the recommendation in `PRODUCT_REVIEW.md`.

## Phase 3 — Real data: aggregate market trends (done)

**Decision (2026-09-22):** per-listing history (this exact address's price
drops) isn't obtainable for free or legally - no free source backfills
individual listing/relisting history, and scraping the sites that have it
violates their ToS (Craigslist successfully sued PadMapper for exactly
this product idea). Paying a licensed provider was explicitly off the
table. Pivoted to real, free, legal **aggregate market-trend data by
metro** instead - a genuine scope change ("any address's history" becomes
"how a market/segment is moving"), surfaced and agreed on explicitly.

### Sources

| Source | Status | Notes |
|---|---|---|
| Redfin Data Center | **In production** | Price Drops, Home Delistings & Relistings, Housing Market Tracker. Metro-level, top 50 metros, monthly, Jan 2012 - Aug 2026 (176 months). Downloads page is bot-gated for automation (403, confirmed via headless browser) but works in a real browser. |
| Apartment List | **In production (rent side)** | Rent Estimates (split by bed size), Vacancy Index, Time on Market. Jan 2017/2019 - Aug 2026. Pulled as direct CDN links, no bot-gate. Metro naming doesn't match Redfin's, and isn't even consistent across Apartment List's own files (one file suffixes " Metro Area", others don't) - see the crosswalk bug below. |
| Census ACS (`api.census.gov`) | **Pending - free key, signup issues** | Two signup attempts: validation email either didn't arrive or the one-time link was already invalid by the time it was clicked. Not blocking anything - Apartment List already covers the rent-trend need. Would add an independent, annually-updated benchmark (different methodology: surveys *all* current renters, not just new-lease asking prices - a real, useful distinction, not a duplicate). |
| Zillow Research (ZHVI/ZORI) | **Deprioritized** | 403 on every attempt (3 tries). Apartment List covers the same need. |
| HUD Fair Market Rents | **Unverified, low priority** | Annual cadence, same "benchmark not trend" role as Census. |

### What got built

- **Crosswalk** (`backend/app/market_crosswalk.py`): explicit, hand-reviewed
  table, not a fuzzy-match function run at ingest time. 40/50 Redfin metros
  matched to Apartment List cleanly. The other 10 are a real geography
  mismatch: Redfin tracks metropolitan *divisions* (Anaheim, Fort
  Lauderdale, Oakland, ...) that Apartment List only publishes as part of a
  larger combined metro (Los Angeles, Miami, San Francisco, ...). Left
  without rent-side data rather than approximated onto the parent metro -
  Anaheim's rent isn't Greater LA's rent.
- **Schema** (`backend/app/models.py`): `Metro` + `MarketMetric`, a
  long/tidy fact table (one row per metro/period/metric/source) - new
  metrics or sources are new rows, never a migration.
- **ETL** (`backend/app/ingest_market_data.py`): loads all six real CSVs.
  50 metros, 121,218 Redfin rows, 21,963 Apartment List rows.
- **Real bug found and fixed during verification, not before:**
  cross-checking Austin's numbers in the new tables against the
  already-validated raw CSVs, `time_on_market_days` came back empty.
  Cause: that one Apartment List file suffixes every metro name with
  `" Metro Area"`, unlike its own other two files - a silent join failure
  (0 rows, no error) until normalized. Re-ran after the fix; all values
  matched exactly. Worth remembering: every cross-source join in this
  project has had at least one non-obvious naming mismatch, and none of
  them threw an error.
- **Full cutover**: NL layer, API (`GET /metros`, `GET /metros/{id}/series`,
  `POST /query`), and frontend (metro browser, trend charts, ranking
  charts) all rewired to the new schema. Old `Listing`/`ListingEvent`
  model, its router, and its seed script removed outright.
- **Verified in a real browser** (headless Chromium, not just curl): metro
  grid, metro detail charts, NL trend queries, and NL ranking queries all
  render correctly with zero console errors. Two apparent chart bugs
  during testing turned out to be screenshot-timing artifacts (Recharts'
  mount animation, plus a hover-tooltip overlay) - confirmed by checking
  the actual SVG path data and raw network responses before concluding
  anything, not by assuming the first odd screenshot was real.

### Still open
- [ ] Census ACS integration once a key exists.
- [ ] Re-verify Zillow Research / HUD FMR via a real browser - low
      priority, not blocking anything.

## Phase 4 — Engineering rigor
- [ ] Automated backend tests (data model, ETL, API contracts) - distinct
      from the eval set, which tests NL-layer behavior, not general code
      correctness.
- [ ] Frontend component tests
- [ ] CI: run the suite (and the eval set) on every push

## Phase 5 — Deployment
- [ ] Pick a host, wire real CD (auto-deploy on merge to main)
- [ ] Env/secrets management for the deployed environment (see
      `PREFERENCES.md` - verify secrets are actually present post-deploy)

## Phase 6 — Portfolio packaging
- [ ] README/demo polish (short walkthrough, screenshots or a clip)
- [ ] A short writeup connecting this project's decisions to what a
      forward-deployed AI engineer role actually needs

See `PRODUCT_REVIEW.md` for an honest read on where this currently stands
against these phases, and `DOCUMENTATION.md` for the technical reference.
