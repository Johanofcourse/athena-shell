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
- [ ] Wire a real `DEEPSEEK_API_KEY` and run `/query` end to end
- [ ] Build an eval set: ~15-20 representative NL queries with expected
      filter output, scored automatically on every change
- [ ] Handle queries the schema can't answer (e.g. "near good schools" -
      no schools data) by degrading gracefully, not hallucinating a filter
- [ ] Decide the fallback story for ambiguous/ malformed model output
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
| Redfin Data Center | **Confirmed relevant, blocked on access** | Has "Price Drops," "Home Delistings & Relistings," and "Housing Market Tracker" (days on market) as named historical datasets - maps closely onto our existing metrics. Downloads page returns HTTP 403 with a bot-detection challenge, confirmed via a real headless-browser request, even though the data is meant for public download. **Not** going to try to defeat that gate (fingerprint spoofing to get past anti-bot protection is the same category of problem as scraping, regardless of the data being free) - needs a human to click through in a real browser instead. |
| Census ACS (`api.census.gov`) | **Confirmed reachable, needs a free API key** | Direct JSON API, e.g. `B25064_001E` = median gross rent, `B25077_001E` = median home value, queryable by county/state. Anonymous requests now redirect to `missing_key.html` - registration is required but free (`api.census.gov/data/key_signup.html`, confirmed to exist). Once we have a key this is fully scriptable, no human-in-the-loop needed per request. |
| Zillow Research (ZHVI/ZORI) | **Unverified** | Recalled from training as a real free program (home value + rent indices), but live fetch attempts returned HTTP 403. Needs a real-browser check like Redfin, or independent confirmation, before relying on it. |
| HUD Fair Market Rents | **Unverified** | Recalled from training as a real annual free government dataset. Fetch attempts returned no usable content (likely a rendering issue, not necessarily blocked). Needs a follow-up check. |

### Next steps (in-progress, divided by who can actually do them)

- [ ] **Johan:** open the Redfin Data Center downloads page in a real
      browser, download 2-3 files (Price Drops, Home Delistings &
      Relistings, and one Housing Market Tracker export), share them
      (repo `data/samples/`, gitignored, or pasted excerpts) for
      structure/quality review.
- [ ] **Johan:** sign up for a free Census API key, pass it in as
      `CENSUS_API_KEY` (never committed) so pulls can be scripted.
- [ ] **Claude:** once files/key are in hand, inspect real
      columns/granularity/history depth and report back before touching
      the schema.
- [ ] **Claude:** re-verify Zillow Research and HUD FMR via a real
      browser rather than leaving them as "recalled, not confirmed."
- [ ] Redesign `Listing`/`ListingEvent` into a geography x time-series
      shape once the above is confirmed; update `QueryFilters` and the
      frontend (trend/comparison views instead of a listings grid) to
      match.

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
