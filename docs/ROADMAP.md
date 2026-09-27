# Roadmap

Athena Shell has two goals that both need to hold up: a genuinely useful
listing-history search tool, and a portfolio piece that demonstrates
forward-deployed AI engineering skill. Phases below are ordered by what
actually derisks those goals, not by what's easiest to build next.

## Phase 0 — Scaffold (done, PR #1)
- [x] Data model: `Listing` + append-only `ListingEvent` timeline
- [x] Synthetic dataset generator (180 listings, realistic price/relist/sale history)
- [x] REST API: `/listings`, `/listings/{id}`, `/query`
- [x] NL query layer wired to DeepSeek (tool-calling -> validated filter shape)
- [x] React/TS search UI with per-listing history chart
- [ ] Not yet done: actually exercising `/query` against live DeepSeek

## Phase 1 — Prove the NL layer works
The differentiating part of this project, and currently the least proven.
- [x] Guardrails ahead of a live key: `/query` input capped at 300 chars,
      rate-limited to 10 req/min/IP (verified locally - burst of 11
      returns `429`). Still open: no auth, no spend cap on the DeepSeek
      key itself (must be set in DeepSeek's own dashboard once the key
      exists). See `DOCUMENTATION.md` -> Guardrails.
- [x] Wire a real `DEEPSEEK_API_KEY` and run `/query` end to end. Two
      real fixes needed along the way, not a clean first try:
      - Model name was stale (`deepseek-chat` -> `deepseek-flash`,
        confirmed against DeepSeek's docs - "DeepSeek Flash" the
        marketing name maps to `deepseek-flash` the API string).
      - `deepseek-flash` runs in "thinking" mode by default, which
        **rejects forced `tool_choice` outright** (400 error). Fixed by
        passing `extra_body={"thinking": {"type": "disabled"}}` -
        confirmed by testing directly against the API, not from docs
        (DeepSeek's docs didn't cover this interaction).
      - Manually tested 5 varied queries post-fix: price/property-type/
        city/days-on-market/relist-count filters all parsed correctly,
        "cheapest" correctly mapped to a sort clause. Tool-calling itself
        is reliable.
- [ ] Build an eval set: ~15-20 representative NL queries with expected
      filter output, scored automatically on every change. Not built yet
      - the 5 manual tests above are a smoke test, not a real eval.
- [ ] **Real finding from manual testing:** "houses near good schools"
      didn't hallucinate a schools filter (good) but silently dropped
      that part of the query and returned 25 unfiltered results with no
      indication that school quality isn't something this system can
      evaluate. Not hallucinating turned out to be necessary but not
      sufficient - the model also needs to *say* when part of a query is
      unsupported, not just quietly ignore it. Needs a real fix (e.g. the
      tool schema gains an `unsupported_aspects` field the model
      populates, surfaced in `explain_filters()`), not just noting it.
- [ ] Decide the fallback story for ambiguous/malformed model output
- Note: once Phase 3 lands, `QueryFilters` moves from per-listing filters
      to geography/time-series filters - this eval set will need to be
      rebuilt against the new shape, not just extended.

## Phase 2 — Visual redesign
- [ ] Replace the current generic/flat UI with the industrial,
      hazard-signage-inspired direction from `PREFERENCES.md`

## Phase 3 — Real data: aggregate market trends, not per-listing scraping

**Decision (2026-09-22):** per-listing history (this exact address's price
drops) isn't obtainable for free or legally - no free source backfills
individual listing/relisting history, and scraping the sites that have it
(Zillow, Redfin, Craigslist, Apartments.com) violates their ToS. This
isn't hypothetical risk: Craigslist successfully sued PadMapper for
scraping rental listings into a comparison tool - functionally the same
product idea. Paying a licensed provider (ATTOM, Bridge/MLS) would solve
it but is explicitly off the table (no budget).

What's real, free, and legal instead: **aggregate market-trend data by
geography** (metro/zip/county), published directly by Redfin and the
Census Bureau as historical time series - the backfill already exists,
we're not waiting for it to accumulate. This changes the product from
"look up any address's history" to "compare how a market/segment is
moving" - still serves the rent-negotiation mission (citing a published
median-rent trend is arguably more credible leverage than one scraped
comp), but it's a real scope change, not a detail.

### Sources evaluated so far

| Source | Status | Notes |
|---|---|---|
| Redfin Data Center | **Confirmed, files in hand** | Downloads page is bot-gated for automation (403, confirmed via headless browser) but works fine in a real browser. Johan pulled all three: Price Drops, Home Delistings & Relistings, and Housing Market Tracker (key metrics), each Metro-level, top 50 metros, monthly, **Jan 2012 - Aug 2026** (176 months, 8,800 rows/file, ~1MB each). Spot-checked Austin's actual numbers against known history - matches the real 2012 low, 2022 pandemic-boom peak ($535k median, 38-day DOM), and the 2023+ cooldown. In `data/samples/`, committed. |
| Apartment List | **Confirmed, files in hand (rent side)** | Rent Estimates, Vacancy Index, and Time on Market pulled as direct CDN CSV links (Contentful-hosted, no bot-gate - Johan found these via the page's download dropdown). Rent Estimates: Jan 2017-Aug 2026, 642 metro rows, split by bed size (overall/1br/2br), wide format (one column per month, not one row per period like Redfin). Vacancy Index: 125 metro rows, no bed-size split. Time on Market: only 46 metro rows. Spot-checked Austin: rent peaked $1,636 (Aug 2022) then cooled to $1,300 (Aug 2026) while vacancy rose 8.4% -> 9.3% and time-on-market rose 36 -> 41 days - three independent metrics telling the same coherent oversupply story. Two real gotchas: metro naming doesn't match Redfin's ("Austin, TX metro area" vs "Austin-Round Rock-Georgetown, TX"), and isn't even consistent across Apartment List's own files (one has "...TX Metro Area" suffix, others don't) - a real crosswalk/normalization step is needed, not just a join. Coverage also isn't uniform: full three-metric coverage is capped at the 46 metros Time on Market has. In `data/samples/`, committed. |
| Census ACS (`api.census.gov`) | **Confirmed reachable, needs a free API key** | Direct JSON API, e.g. `B25064_001E` = median gross rent, `B25077_001E` = median home value, queryable by county/state. Anonymous requests now redirect to `missing_key.html` - registration is required but free (`api.census.gov/data/key_signup.html`, confirmed to exist). Note: this is an annual (5-year rolling estimate) figure, not monthly like Redfin/Apartment List - useful as a benchmark/cross-check, not a trend line. Once we have a key this is fully scriptable, no human-in-the-loop needed per request. |
| Zillow Research (ZHVI/ZORI) | **Deprioritized** | Every fetch attempt (3 tries across sessions) returned HTTP 403. Apartment List already covers the same need (monthly rent trend) and is confirmed working - not worth continuing to chase Zillow. |
| HUD Fair Market Rents | **Unverified, low priority** | Recalled from training as a real annual free government dataset. Fetch attempts returned no usable content. Annual cadence like Census, so same "benchmark not trend" role - not blocking anything right now. |

### Next steps (in-progress, divided by who can actually do them)

- [x] **Johan:** download the three Redfin files (metro-level, 2012-2026)
      and add them to `data/samples/`.
- [x] **Johan:** download three Apartment List files (Rent Estimates,
      Vacancy Index, Time on Market) via direct CDN links, added to
      `data/samples/`.
- [ ] **Johan:** sign up for a free Census API key, pass it in as
      `CENSUS_API_KEY` (never committed) so pulls can be scripted.
- [ ] **Johan:** get a DeepSeek API key, pass it in as `DEEPSEEK_API_KEY`
      so Phase 1 can actually run.
- [x] **Claude:** inspect all six files' real columns/granularity/history
      depth, spot-check data quality against known real-world market
      history. Confirmed good on all six - see table above.
- [ ] **Claude:** re-verify Zillow Research and HUD FMR via a real
      browser rather than leaving them as "recalled, not confirmed."
      Low priority - Apartment List + Census already cover the need.
- [ ] Build a geography name crosswalk (Redfin metro names <-> Apartment
      List metro names, which aren't even consistent with themselves
      across files) - this has to exist before anything can join across
      sources, not an afterthought.
- [ ] Design and build the geography x time-series schema (replacing
      `Listing`/`ListingEvent`) and the ETL to load these six CSVs into
      it (note: Apartment List's files are wide-format, one column per
      month - need reshaping, unlike Redfin's long format); update
      `QueryFilters` and the frontend (trend/comparison views instead of
      a listings grid) to match. Not started yet.

## Phase 4 — Engineering rigor
- [ ] Automated backend tests (data model, filter logic, API contracts)
- [ ] Frontend component tests
- [ ] CI: run the suite on every push

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
