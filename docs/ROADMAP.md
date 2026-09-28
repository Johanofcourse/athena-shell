# Roadmap

Athena Shell has two goals that both need to hold up: a genuinely useful
market-trend tool, and a portfolio piece. The portfolio goal rests on
three deliberate pillars (stated explicitly 2026-09-27), each chosen
because Apollo Shell (the prior project) didn't cover it:

1. **React + TypeScript frontend** - Apollo Shell was Flask/Jinja,
   server-rendered, no modern frontend framework at all.
2. **Real LLM/AI integration, done properly** - structured tool-calling
   over real data, not a bolted-on chatbot. The "forward-deployed AI
   engineer" angle. See Phase 1.
3. **Real user accounts + payments** - Apollo Shell has zero auth, zero
   multi-user support, zero billing. Meant to demonstrate real SaaS
   patterns (auth, multi-tenancy, billing), not a minimal login gate.
   Foreshadowed in `PREFERENCES.md` ("real payment/auth credentials are
   coming") but not scoped as its own phase until now - see Phase 7.
   **This was previously tracked as an accepted "no auth" limitation in
   `PRODUCT_REVIEW.md`; that undersold it. It's a co-equal pillar, not a
   nice-to-have, and shouldn't be left deprioritized indefinitely the way
   the visual redesign was for a while.**

Phases below are ordered by what actually derisks these goals, not by
what's easiest to build next.

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
- [x] **Persistent free-tier quota** (10 queries/IP/UTC day, `QueryUsage`
      table): the burst limiter above resets every minute and doesn't cap
      overall usage - this does. Checked before the paid DeepSeek call, so
      a rejected request costs nothing. Honest rejection message (no
      subscription mentioned, since none exists yet) rather than a fake
      paywall pointing at a Phase 7 feature that isn't built - this table
      is meant to be the actual foundation Phase 7 builds tier enforcement
      on top of later. Verified at the real boundary against the live
      endpoint: 10th call succeeds, 11th returns 429 without reaching
      DeepSeek.
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
- [x] **Stress-tested it**, deliberately trying to break the 18/18 rather
      than treat it as done: expanded to 26 cases (off-topic input, a
      prompt-injection attempt, a typo, a self-contradictory ranking
      question, weird casing, a relative time range) plus a repeatability
      check (same ambiguous query, 5 runs). Result: **26/26 cases, 59/59
      checks, 5/5 repeatability**. Read this as "didn't find a failure
      this round," not "solved" - passing every adversarial case on the
      first attempt is at least as likely to mean the cases weren't hard
      enough as it is to mean genuine robustness. See
      `PRODUCT_REVIEW.md` for what harder testing would look like next.
- [x] **Three AI-capability extensions**, all verified live, not just
      built: (1) a transparency panel showing the exact resolved
      `MarketQueryFilters` DeepSeek produced - the tool-calling
      architecture always made this auditable in principle, this is where
      it becomes visible; (2) a thumbs up/down feedback widget logging
      `{query, filters, rating}` to a new `QueryFeedback` table - real
      material for growing the eval set from production usage rather than
      only hand-written cases; (3) multi-turn conversation support -
      prior turns are replayed as real user/assistant/tool messages
      (OpenAI-compatible format), verified to both carry context forward
      ("what about Denver?" correctly keeps the prior metric) and
      override it when asked (a follow-up correctly swaps the metric
      while keeping the metro).
    - **Real bug found while verifying multi-turn, not before:**
      `bed_size` (only meaningful for `median_rent`) could get carried
      over from a rent question into a follow-up about an unrelated
      metric, silently zeroing out real results (every non-rent metric is
      stored with `bed_size=NULL`, so filtering on a stale "overall"
      value finds nothing) - the exact "no_data" honesty path firing for
      the wrong reason. Fixed with a deterministic sanitize step in
      `interpret_query()` (not a prompt-wording fix, which wouldn't
      guarantee it every time) and added as a permanent regression case
      in the eval set.
    - **Re-running the full eval after this work found a second, real,
      independent issue**: `adversarial_off_topic` failed on that run
      (26/27) - re-tested 10x afterward and it recurred roughly 1-in-6
      times. When it happens, `unsupported_aspects` comes back empty
      instead of flagging the request - but the model still never
      fabricates data (metros stays empty, metric defaults to something
      inert), so it falls through to the existing "no metro specified"
      message rather than anything misleading. Low severity, real, and
      exactly the kind of thing this eval exists to keep finding.
    - **Fixed the same day, not left open**: strengthened `SYSTEM_PROMPT`
      to explicitly require `unsupported_aspects` to describe the request
      even when the *entire* question is off-topic, not just leave it
      empty. Re-tested 10/10 clean afterward (up from ~5/6). Full suite
      re-run: **27/27 cases, 62/62 checks** - and the repeatability check
      on the *same run* reproduced the metric-choice variance seen only
      by hand before now (2 different metrics across 5 runs, vs. 5/5
      stable the run before) - real, recurring, non-determinism, not a
      one-off anecdote, and not something a prompt fix should be expected
      to eliminate the way the bed_size fix structurally did.

## Phase 2 — Visual redesign (done)
- [x] Replaced the generic/flat UI with the industrial, hazard-signage
      direction from `PREFERENCES.md` - dark theme, stencil display type,
      monospace data readouts, hazard-stripe accent, sharp corners.
      Verified in a real browser at every step, not just visually eyeballed
      once: caught and fixed a genuine readability bug along the way
      (crowded, overlapping X-axis date labels on the long time-series
      charts - fixed with an explicit tick interval, tuned again after a
      later request to show full 4-digit years).
- [x] Fixed a real UX gap found during review: there was no way back from
      NL query results to the metro browse grid except reloading the page.
      Added a "back to browse" link and a clickable logo, both verified to
      actually work, not just added.
- [x] Metric-aware value formatting (currency, percent, plain number - see
      `DOCUMENTATION.md` -> Frontend) and a deterministic per-result
      analysis summary, both added in response to live review feedback.

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
| Census ACS | **In production (income + gross-rent fallback)** | The `api.census.gov` API key signup never worked (multiple attempts, two different emails, validation link consistently broken/unreceived - a known, documented issue with institutional email scanners rewriting the one-time link). **Worked around entirely** by using `data.census.gov`'s own table browser to download CSVs directly - no API key needed at all, same "manual browser download" pattern that worked for Redfin/Apartment List. Table `B19013` (median household income), 5-Year 2024 estimate, all 50 metros crosswalked (40 direct, 10 genuine gaps) - spot-checked (Austin $100,431). Table `B25064` (median gross rent), 5-Year 2024, county-level, for the 10 metro-division metros only - a deliberately narrower fallback used to fill the `median_rent` gap, always flagged as an approximation. `S0801` (commute time) not pursued this round - see Still open. |
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

### Census income + gross-rent fallback + rent-to-income (done, 2026-09-28)
- [x] **Third crosswalk entry added** (`census_income_name` on `Metro`):
      matched all 50 metros against Census's B19013 metro-name column
      headers using the same first-city-token + state-overlap heuristic as
      the original Redfin/Apartment List crosswalk, then hand-reviewed.
      40/50 matched cleanly with zero ambiguity (confirming the
      "Austin-Round Rock-San Marcos" / "Denver-Aurora-Centennial" boundary
      drift noted below is real but didn't break the heuristic). The other
      10 are the exact same metro-division metros already missing
      `aptlist_name` - Census's metro-level income table only publishes
      the larger combined metro too, so left as a genuine gap rather than
      borrowed from the parent metro, consistent with the existing
      rent-side precedent.
- [x] **Census median household income** (`median_household_income`,
      `MetricSource.CENSUS`): ingested from the B19013 5-Year 2024
      estimate as a single snapshot per metro (not a monthly series - the
      shared fact table handles a one-point "series" fine). 40 rows.
      Spot-checked: Austin $100,431, matching the earlier manual check.
- [x] **Median rent honesty fallback** (`median_gross_rent`,
      `MetricSource.CENSUS`): for the same 10 metro-division metros,
      county-level Census gross rent (table B25064, since metro divisions
      are officially defined as whole counties) substitutes for the
      missing `median_rent` - always under its own metric name, never
      silently relabeled, and only offered for bedroom-unspecific
      questions (Census doesn't split by bed size). `run_market_query`
      returns a new `approximated_metros` list whenever this fires, and
      `explain_filters()` surfaces it as an explicit caveat. Applied on
      both the NL query path and the metro-detail-panel browsing path
      (`GET /metros/{id}/series`), so the two never disagree about
      whether a metro "has" rent data.
- [x] **Rent-to-income ratio** (`rent_to_income_pct`, computed): (median
      rent x 12) / median household income, as a percent. Income is a
      single snapshot held constant across whatever rent periods exist -
      a real combination of two real numbers, not a fabricated trend.
      Metros missing either leg are reported as `no_data_metros`, never
      silently dropped or blended.
- [x] Verified end to end: direct `run_market_query` checks (Austin
      income, Anaheim rent fallback, Anaheim income gap, Denver
      rent-to-income trend, cross-metro ranking, bed-size-specific rent
      with no fallback offered), the full eval suite (**31/31, up from
      27/27** - 5 new cases), a multi-turn sanitize check (bed_size
      correctly cleared switching into `rent_to_income_pct`), and a real
      browser (the metro grid's new "Income data" badge, Anaheim's detail
      panel now showing a flagged fallback chart instead of "no data",
      and a live rent-to-income ranking query rendering correctly).

### Still open
- [ ] Census `S0801` (commute time) - the API key signup issue from
      before is unresolved; not pursued further this round since Johan
      deferred pulling more Census tables for now.
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

## Phase 7 — Real user accounts + payments
Numbered last, but a **co-equal pillar** with Phases 1-2 (see the top of
this file) - not a nice-to-have to fit in if time allows. The point is
real SaaS patterns, not a minimal login gate:
- [ ] User accounts (signup/login, real session handling - JWT or
      server sessions, per `PREFERENCES.md`'s mention of "session/JWT
      secrets")
- [ ] Multi-tenancy: decide what's actually scoped per-user on a tool
      that's fundamentally about shared public market data - likely
      saved searches, watched metros, or query history, not the
      underlying data itself. Worth a real design pass, not an assumption.
- [ ] Real payments (Stripe per `PREFERENCES.md`) gating *something*
      concrete - decide what tier/feature split actually makes sense
      before wiring billing to it.
- [ ] Threat-model this properly once real accounts and payment data
      exist - `PREFERENCES.md` calls out that secrets discipline "matters
      even more here" once this lands.

See `PRODUCT_REVIEW.md` for an honest read on where this currently stands
against these phases, and `DOCUMENTATION.md` for the technical reference.
