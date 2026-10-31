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

### Ranking by rate of change, not just latest value (done, 2026-10-11)
- [x] **Real bug, flagged and deliberately left open rather than patched
      inline, now fixed properly.** First noticed while building
      `total_population` (see Phase 3): "which metros are growing/rising
      fastest" silently resolved to `sort_by: "value"` - ranks by latest
      *absolute* value, not rate of change - because `"value"` was the
      only ranking mode that existed. Confirmed not population-specific
      at the time: `median_rent` had the identical problem (ranked by
      current rent level, called it "fastest-rising"). Fixed now with a
      third ranking mode, `sort_by: "change"`, across the whole query
      system - the scope the original finding called for, not a
      population-specific patch.
- [x] `run_market_query` computes percent change over each metro's
      available history (respecting `start`/`end`) rather than a single
      snapshot value, needing at least two real points to compute a rate
      from - a metro with only one data point (every single-snapshot
      metric: income, commute, property tax, hazard risk score) correctly
      comes back as `no_data_metros` when explicitly named, not a crash
      or a nonsense 0% change.
- [x] The returned value for `"change"` mode is the computed percent
      change itself, not a raw metric value - `RankingChart.tsx`'s axis
      and tooltip, and both narrative-grounding functions
      (`summarize_metric_facts` / `summarizeResults`), needed their own
      percent-only formatting rather than the metric's normal unit
      formatter, which would otherwise render e.g. a population's percent
      change as if it were a population count.
- [x] **Verified live against the exact phrasing that originally exposed
      the bug.** "Which metros have rent prices rising the fastest" and
      "which metros are growing the fastest in population" both now
      correctly resolve to `sort_by: "change"` and rank by percent change
      (Providence, RI +113.0% leading rent growth; Charlotte, NC +57.5%
      leading population growth) - confirmed via the real API response
      and a Playwright screenshot of the rendered chart showing
      percent-formatted axis/tooltip (`+0.0%` … `+120.0%`, `+113.0%` in
      the tooltip), not dollar or population-count formatting. Also
      confirmed a single-snapshot ranking question ("which metros have
      the highest median income?") still correctly resolves to
      `sort_by: "value"`, not `"change"`.
- [x] 5 new backend tests, 2 new frontend tests, 3 new eval cases (two for
      the exact phrasings that exposed the bug, one confirming `"value"`
      mode is still chosen for a single-snapshot metric).

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

### Palette refresh + geographic metro map (done, 2026-09-30)
Real feedback from a real viewer Johan showed the app to: the hazard-
yellow/black look read as literal caution tape ("looks like a
construction site"), fighting a real-estate app's positioning.
- [x] Re-colored the theme tokens (`--accent` to a vivid blue, `--danger`
      to a vivid red) rather than abandoning the industrial identity -
      same dark, high-contrast, sharp-corner bones from Phase 2, just
      re-colored. Every component keyed off the CSS variables updated
      for free; `TrendChart.tsx`'s multi-series line palette was
      hardcoded separately and needed a matching fix, now leads with the
      theme tokens directly so it can't drift out of sync again.
- [x] Replaced the metro browsing grid with an accurate, data-driven US
      map (`UsMetroMap.tsx`, `react-simple-maps` + `d3-geo` +
      `us-atlas`'s real Census TIGER/Line-derived topology) alongside a
      synced city list, not an illustrated/isometric map - that style
      is normally hand-drawn art, not something coordinate data gets you
      to, and would have been a real-vs-fabricated tradeoff this project
      doesn't make elsewhere.
- [x] **A fifth naming convention, and the first with zero gaps**:
      `METRO_COORDINATES` (`market_crosswalk.py`), sourced from the
      Census Bureau's own Gazetteer files - CBSA centroids for the 40
      combined metros, and the actual named city's point (from the
      Place gazetteer) for the 10 metro-division metros, since a
      division isn't its own CBSA entry. Two of those ten are counties
      rather than incorporated cities (Montgomery County PA, Nassau
      County NY), so they use a real named place within the county
      (Norristown, Hempstead) instead of a fabricated "county centroid."
- [x] `GET /metros` now returns `latitude`/`longitude` for every metro.
      A CBSA centroid is a real geometric area centroid, not a
      population-weighted "downtown" point, so a large/sprawling
      metro's dot can land somewhat inland of its named city (e.g.
      Seattle) - that's the data honestly reflecting the area's real
      shape, not an error worth hiding.
- [x] Verified: 2 new backend tests (coordinate coverage + sanity
      bounds), a real browser check of map rendering (all 50 pins,
      correct Alaska/Hawaii inset positioning, real density clusters
      matching known geography), hover/click interaction on both the
      map pins and the list, and confirming both paths correctly open
      the same metro detail panel. Map rendering itself isn't unit
      tested, same reasoning as the Recharts trend/ranking charts -
      SVG/topology rendering is real-browser-verification territory,
      not jsdom's.

### Inverted-pyramid answer layout + source citations (done, 2026-10-11)
Johan: "a nice summary as a header... followed by backing data and
graphs... most important info on top, then important details, then
general info and background/citations and graphs numbers at the bottom...
present facts and data and people can interpret it, how they see fit,
like in articles." The inverted-pyramid structure journalism uses -
thesis first, supporting evidence last.
- [x] Reordered `QueryResults.tsx`'s metric-query path to match:
      narrative (the thesis - already existed, just wasn't actually
      first) -> the filter-echo/caveat line (`explanation`) -> a new
      source citation -> chart, with the chart now the last thing someone
      sees, not the second. The synthesis prompt already enforced
      "describe what happened, not why" (no editorializing), so the
      facts-first framing Johan asked for didn't need a prompt change -
      only the layout was working against it.
- [x] **Added the citation line itself, which didn't exist for metric
      queries before this.** A metric's real source (Redfin, Apartment
      List, Census ACS, BLS, FHFA/FRED, Freddie Mac PMMS, FEMA NRI)
      previously only lived inside `METRIC_DESCRIPTIONS` - tool-schema
      hint text for the model, never shown to the person reading the
      answer. New `METRIC_SOURCES` dict + `source_citation()` mirror the
      commentary path's own "Source: HUD Comprehensive Housing Market
      Analysis..." line, which metric queries never had an equivalent
      of. Handles the one real dual-source case correctly: a rent query
      that fell back to Census gross rent for some metros cites both
      sources, not just Apartment List, which would misattribute the
      number.
- [x] Verified: 3 new backend tests for `source_citation`, 3 new frontend
      tests - one specifically asserting DOM order (narrative before
      explanation before citation before chart), not just presence, so a
      future change that silently reorders these back toward
      graph-first doesn't slip through unnoticed.

### Mobile metro list overflow fix (done, PR #79, 2026-10-11)
Johan: "in mobile the list of top 50 metros is squeeze a bit and the
word on the far right end 'income' is chopped in half."
- [x] Root cause, confirmed by measuring a real row rather than guessing:
      two separate, stacked instances of the same CSS default fighting
      the layout. `.metro-list-name` is a flex child with
      `white-space: nowrap`, and flex items default to
      `min-width: auto` ("never shrink below the text's own full
      width") - the single longest name among all 50 metros (Montgomery
      County, PA, 203px) was forcing every row to need 397px total on a
      ~350px grid column. Fixing just that wasn't enough: `.metro-list`'s
      `grid-template-columns: 1fr` has the identical default at the
      grid-track level, so the column itself stayed locked to 397px
      regardless of the flex-level fix - confirmed via `getComputedStyle`
      showing the first fix correctly applied but having zero effect on
      the actual rendered width until the second, grid-level fix was also
      added.
- [x] Fixed both: `minmax(0, 1fr)` on the grid track, `min-width: 0` +
      `overflow: hidden` + `text-overflow: ellipsis` on
      `.metro-list-name`. Verified by measuring the actual Montgomery
      County row before/after (397px -> 350px) and confirming
      `document.body.scrollWidth` now equals the viewport width (zero
      horizontal overflow, was 27px over before) - not just eyeballing a
      screenshot.
- [x] Merged and verified live.

### Real antique map engraving replaces the vector topology map (done, 2026-10-12)
Johan: "could we maybe use an old public domain USA map and then impose
the pins of the 50 metros on top?" The prior map (Phase 2,
2026-09-30) was already styled to *look* antique, but it was a Census
TIGER/Line vector outline underneath, not an actual historical map -
this replaces it with a real one.
- [x] **Sourced, not generated or assumed**: evaluated five real,
      verified-public-domain 19th-century US map scans (Wikimedia
      Commons / David Rumsey / Library of Congress), shown to Johan
      before picking one - two were ruled out for not covering the West
      Coast at all (predating the Mexican-American War's territory
      gains), one for reading as a railroad advertisement rather than a
      reference map. Landed on an 1870s Colton's "United States of
      America" atlas plate - full lower-48 coverage, soft hand-colored
      engraving that fits the existing gold-frame/parchment design.
- [x] **A real georeferencing problem, not glossed over.** A historical
      engraving has no geodetic projection to plug real lat/long into
      directly, and a first attempt at a single global 2nd-degree
      polynomial fit (from ~28 reference points) produced large, uneven
      pixel errors (mean 115px, worst case 380px) once plotted back onto
      the scan. Switched to a thin-plate spline - the standard GIS
      technique for georeferencing a non-uniformly-distorted scan, exact
      at every reference point rather than forcing one global curve
      through all of them - after expanding to ~39 reference points
      (reading tick marks the map itself prints for a few, reading
      labeled city positions for the rest, both cross-checked against
      each other) for full regional coverage, including corrections
      after a couple of reference points were first misread against the
      wrong region of the scan.
- [x] **Verified by rendering all 50 pins back onto the source scan**,
      not just trusting the math - checked region by region (West Coast,
      Mountain West, Texas, Midwest, Northeast, Southeast, Florida)
      against real geography, not a spot check. Philadelphia, NYC,
      Boston, Baltimore, and DC all land in their correct relative
      positions in the dense Northeast cluster; Chicago lands exactly at
      Lake Michigan's southern tip; the Florida peninsula (Tampa, Miami,
      Key West) is correctly covered despite needing its own dedicated
      reference points the first anchor set didn't include.
- [x] `UsMetroMap.tsx` rewritten: the image is locked to its own aspect
      ratio via CSS (`aspect-ratio`) so it can never letterbox inside its
      wrapper, which the percentage-based pin coordinates
      (`mapCoordinates.ts`) depend on to land correctly - pins are plain
      positioned buttons now, not SVG markers, keeping the same
      hover-pulse/click behavior as before. `react-simple-maps`,
      `d3-geo`, and `us-atlas` are no longer used anywhere and were
      removed from `package.json`.
- [x] Verified in a real browser, not just by the math: desktop and
      mobile screenshots (zero horizontal overflow on mobile, same as
      the fix above), hover state correctly pulses and darkens a pin,
      and a click correctly opens the metro detail panel.

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
| Census ACS | **In production (income + gross-rent fallback)** | The `api.census.gov` API key signup never worked (multiple attempts, two different emails, validation link consistently broken/unreceived - a known, documented issue with institutional email scanners rewriting the one-time link). **Worked around entirely** by using `data.census.gov`'s own table browser to download CSVs directly - no API key needed at all, same "manual browser download" pattern that worked for Redfin/Apartment List. Table `B19013` (median household income), 5-Year 2024 estimate, all 50 metros crosswalked (40 direct, 10 genuine gaps) - spot-checked (Austin $100,431). Table `B25064` (median gross rent), 5-Year 2024, county-level, for the 10 metro-division metros only - a deliberately narrower fallback used to fill the `median_rent` gap, always flagged as an approximation. `S0801` (mean commute time), `B25103` (median property tax), and `B01003` (total population) added later - see the "Four new metrics" section below. |
| Freddie Mac PMMS | **In production (national mortgage rates)** | `www.freddiemac.com/pmms/docs/PMMS_history.csv` - a plain, directly-linked public CSV with zero bot-gating (confirmed: a clean 200, not a 403/challenge), unlike every other source above. Pulled directly rather than through a manual browser step, since there's no protection being routed around - the same distinction this project has drawn throughout (avoiding bot-gate evasion, not avoiding `curl` categorically). Weekly, 1971-present, 30-year fixed/15-year fixed/5-year ARM. |
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

### National mortgage rates (done, 2026-09-30)
- [x] **First genuinely national (non-metro) series**: Freddie Mac's PMMS
      mortgage rate history. Given its own table, `NationalMetric`
      (`backend/app/models.py`) - `(period, source, metric, value)`, no
      metro dimension at all - rather than forcing it into `MarketMetric`
      via a fake "United States" `Metro` row, which would have shown up
      oddly in the metro browsing grid and made the honesty-flag columns
      (`has_rent_data` etc.) meaningless for it. `period` is the real
      weekly reported date, not bucketed to first-of-month like
      `MarketMetric` - no reason to throw away real granularity.
- [x] Three headline series ingested (30-year fixed, 15-year fixed, 5/1
      ARM) - not Freddie Mac's points/margin/spread columns, same
      "measured values only" reasoning as skipping Redfin's precomputed
      YOY columns. 5,659 rows. Real, unforced data quirk found and left
      visible rather than smoothed over: the 5/1 ARM series stops dead
      at November 2022 (Freddie Mac discontinued it) - a query for the
      latest ARM rate honestly returns a 2022 value rather than silently
      extrapolating or erroring.
- [x] `query_market_metrics` gained a new class of metric with no metro
      concept at all - `_sanitize_filters` now also clears `metros` when
      one of these is selected (same deterministic-guardrail pattern as
      the `bed_size` fix), and `explain_filters` was fixed to stop
      claiming to be "ranking across all metros" for a single national
      series in ranking mode - a real phrasing bug caught immediately by
      testing this by hand before it shipped.
- [x] Verified: 7 new backend tests, a frontend formatting test, 2 new
      eval cases (including one confirming a metro named in the question
      gets correctly dropped), and a real browser check of the rendered
      chart, explanation, and analysis summary.

### Still open
- [ ] Re-verify Zillow Research / HUD FMR via a real browser - low
      priority, not blocking anything.

### BLS metro-level unemployment rate (done, 2026-09-30)
- [x] **A genuinely different, legitimate access path solved a gap this
      project had given up on.** BLS's bulk LAUS file was bot-gated
      earlier (only the `la.area`/`la.area_type`/`la.series` reference
      files got through, never the actual data). The registered public
      API (`api.bls.gov`, free key from `data.bls.gov/registrationEngine`,
      stored in `.env`, not committed) is a completely different,
      intended-for-this access method - not scraping-adjacent - and
      worked on the first real request.
- [x] **A fourth independent naming/coding convention**, matched using
      the already-downloaded (but previously unusable) `la.area`
      reference file: BLS area codes, keyed by `metro_id` in a new
      `BLS_AREA_CODES` dict (`market_crosswalk.py`) - a plain lookup, not
      a 7th crosswalk column, since it's used to construct API series
      IDs directly rather than matched against a downloaded file's
      column headers. 49/50 matched automatically via the same
      first-city-token + state heuristic as every other crosswalk here;
      one (New Brunswick, which BLS files under "Lakewood-New Brunswick,
      NJ") needed a manual match.
- [x] **Real, unexpected win**: unlike Apartment List and Census's income
      table, BLS's LAUS genuinely publishes metropolitan *divisions*
      separately (area type "C") - so all 10 of the metro-division gap
      metros (Anaheim, Fort Worth, etc.) got **real, non-approximated**
      unemployment data, not another fallback. Confirmed live: Anaheim
      and Montgomery County, PA both return real division-specific
      values, and Montgomery County, PA appeared in a real "lowest
      unemployment" ranking query in the actual UI.
- [x] Ingest kept offline and deterministic like every other source:
      `fetch_bls_unemployment.py` makes the one live API call (all 50
      metros in a single request - 50 series per query is exactly the
      registered-key limit) and saves the raw response to
      `data/samples/bls_unemployment_rate.json`; the actual
      `ingest_bls_unemployment()` only ever reads that saved file, run
      manually/occasionally like the Redfin/Apartment List refresh, not
      on every ingest. 8,703 rows, Jan 2012 - Jul 2026, plain per-metro
      `unemployment_rate` metric - no new query-logic branch needed, it
      fits the existing generic path exactly like every other per-metro
      metric.
- [x] Verified: 5 new backend tests (ingest parsing + crosswalk
      invariants), 2 new eval cases, a live `curl` check, and a real
      browser screenshot of a ranking query.

### FHFA house price index via FRED (done, 2026-09-30)
- [x] A sixth data source (**FRED**, the St. Louis Fed's economic data
      API - itself a republisher of real underlying sources like FHFA,
      not a source unto itself), added the same night as BLS, for a
      genuinely independent home-price benchmark alongside Redfin's own
      median sale price - a repeat-sales index vs. a median transaction
      price, methodologically different on purpose, never blended with
      Redfin's numbers under one label.
- [x] **A fifth naming/coding convention** (`FHFA_HPI_SERIES_IDS`,
      `market_crosswalk.py`), matched via FRED's own API metadata (series
      titles), same pattern as `BLS_AREA_CODES` - a plain lookup, not a
      crosswalk column, used to call FRED's API directly.
- [x] **A real, meaningfully different coverage gap, surfaced and
      discussed before building, not discovered after:** unlike BLS,
      FHFA doesn't publish one combined index for large multi-division
      metros at all - Los Angeles, Chicago, San Francisco, Seattle,
      Washington DC, Miami, Philadelphia, Dallas, and Detroit are
      genuine gaps, not approximated from one division (a division's
      number isn't the combined metro's number - the same reasoning as
      every other metro-division gap in this project). Three of the 10
      metro-division gap metros (Anaheim, Montgomery County PA, New
      Brunswick) also have no current FHFA division series. **38/50
      real matches** - decided deliberately with Johan mid-build once
      the actual coverage picture was known, not defaulted into.
      Existing `no_data_metros` honesty path covers all 12 gaps with no
      new mechanism needed.
- [x] Same offline/deterministic ingest pattern as BLS:
      `fetch_fred_house_price_index.py` makes 38 live API calls (FRED's
      endpoint takes one series per request, unlike BLS's batch
      endpoint) and saves the raw responses; `ingest_fhfa_hpi()` only
      reads that saved file. 2,186 rows, quarterly, Jan 2012-present.
      `house_price_index` is a plain per-metro `MarketMetric` - no new
      query-logic branch, and the tool-schema description explicitly
      tells the model it's an index value, not a dollar amount.
- [x] Verified: 5 new backend tests, 2 new eval cases (including one
      confirming Los Angeles correctly returns a genuine gap, not a
      substituted division number), a live `curl` check, and a real
      browser screenshot showing Austin's well-documented 2022 price
      peak in the actual rendered chart.

### Four new metrics: commute, property tax, population, hazard risk (done, 2026-10-11)
Picked up from the disclaimer Johan noticed: "This system can't evaluate:
... non-market quality-of-life factors (lifestyle, safety, commute,
amenities)." Looked into real, verifiable sources for commute and safety
both - safety (crime) turned out to have a serious coverage gap (California,
New York, Pennsylvania, and Florida essentially don't participate in the
FBI's NIBRS program as of 2025, which would mean no data for NYC, LA, SF,
Miami, Philadelphia - exactly the metros people ask about most), so Johan
chose to skip that for now. The other three Census/FEMA pulls below had no
such problem.
- [x] **`mean_commute_minutes`** (Census ACS 5-Year 2024, Table S0801):
      mean travel time to work in minutes, per metro - same CBSA geography
      and metro-name format `median_household_income` already uses,
      reusing the existing `census_income_name` crosswalk, no new one
      needed.
- [x] **`median_property_tax`** (Census ACS 5-Year 2024, Table B25103):
      median annual real estate taxes paid by owner-occupied households,
      per metro - same pipeline and crosswalk as commute. Added to the
      currency-formatting set (`frontend/src/format.ts` and
      `nl_query.py`'s `_CURRENCY_METRICS`).
- [x] **`total_population`** (Census ACS **1-Year** Table B01003, not the
      Population Estimates Program originally assumed - confirmed by
      testing directly against the API that PEP's metro-area geography
      support is inconsistent across vintages, present in 2019, silently
      dropped from 2021). The first of these four that's a genuine
      multi-year trend (2012-2024, except 2020 - ACS 1-Year wasn't fielded
      normally that year because of COVID-19, left as a real gap rather
      than interpolated), not a single snapshot.
    - **Real correctness bug caught before shipping, not after:** OMB
      revises CBSA names periodically, and Austin alone was named three
      different ways across this date range ("Austin-Round Rock-San
      Marcos" in 2012, "Austin-Round Rock" in 2013, "...-Georgetown"
      2019-2022, back to "...-San Marcos" 2023-2024) - all the same
      metro. A first version of the ingest matched purely by name (like
      income/commute/property-tax reasonably do, since those only ever
      use one year), which silently dropped 10 of Austin's 12 years and
      surfaced as a genuinely wrong narrative: "how has population
      changed in Austin over the last decade" returned only 2023-2024 and
      claimed "grew modestly" based on a single year's difference. Fixed
      by matching on the CBSA's stable numeric code instead of its name.
      Verified against the exact query that exposed the bug: Austin now
      correctly shows all 12 years and a narrative reading "grew by about
      39%... from roughly 1.83 million to 2.55 million."
    - This is also the metric whose ranking question ("which metros are
      growing fastest") first surfaced the `sort_by` rate-of-change bug
      fixed above in Phase 1 - confirmed at the time not to be
      population-specific (median_rent had the identical problem) and
      deliberately scoped out of this change as a separate, later fix.
- [x] **`natural_hazard_risk_score`** (FEMA National Risk Index, December
      2025 release): a composite 0-100 national-percentile score per
      county across 18 natural hazards (flood, wildfire, hurricane,
      earthquake, and others). No live API exists for this source
      (FEMA's own OpenFEMA listing: "OpenFEMA API: N/A. Files Only.") -
      `fetch_fema_nri.py` downloads the bulk county CSV instead.
    - **A real methodology choice, stated plainly in the metric's own
      description so the model doesn't misrepresent it.** NRI publishes
      at county level, not metro level, so one number per metro means
      aggregating a CBSA's constituent counties - done as a
      **population-weighted** average (via the official OMB July 2023
      CBSA-to-county delineation file), not a simple average, so a
      sparsely-populated outlying county can't pull a metro's score
      around as much as its dense urban core. The difference is directly
      exercised by a test (50 and 90 across two counties averages to 70
      unweighted, but weights to 80 once one county has 3x the other's
      population).
    - Two real things found and fixed while building this: FEMA's CDN
      (Akamai) returns a 403 to every `urllib` request regardless of
      headers while `curl` succeeds unconditionally (TLS/HTTP-stack
      fingerprinting, not a header `fetch_fema_nri.py` could set around) -
      worked around by shelling out to `curl` for this one download. The
      CBSA delineation file is only published as `.xlsx` - extracted to a
      plain CSV once rather than adding `openpyxl` as a new runtime
      dependency for a reference file this static.
    - Verified against the real, fully-aggregated data: "which metros
      have the highest natural disaster risk?" ranked California metros
      at the top and Virginia Beach lowest, matching real-world hazard
      geography.
- [x] All four flow through the existing generic per-metro query path and
      the existing trend-chart/ranking-chart/narrative machinery with
      zero metric-specific special-casing (`total_population`) or close
      to it (the other three are single-snapshot, same shape as
      `median_household_income`).
- [x] Verified end to end for all four: 9 new eval cases (one single-metro
      and one ranking/compare case per metric, covering the new tool-
      choice surface area), and the running backend/frontend test totals
      climbed from 113/34 (commute) to 114/34 (hazard risk) across the
      four commits, each with its own metric-specific correctness tests
      (the Austin rename regression, the population-weighting
      discrimination test).

## Phase 4 — Engineering rigor (done, 2026-09-28)
Deferred seven times before this (see `PRODUCT_REVIEW.md`) - done now, not
an eighth deferral.
- [x] **Backend test suite** (`backend/tests/`, pytest, 60 tests, 0.68s,
      zero external API calls): `test_query_logic.py` covers the
      deterministic pieces of `nl_query.py` the eval suite only exercises
      *indirectly* through whatever filters DeepSeek happens to produce -
      the median_rent fallback, the rent_to_income_pct math (checked
      against exact values), `explain_filters`' text for every honesty
      behavior. `test_crosswalk.py` checks structural invariants on
      `market_crosswalk.py` (unique ids/names, the rent-gap and
      income-gap sets are identical). `test_ingest.py` runs the ETL
      functions against tiny fixture CSVs, including a regression fixture
      for the real " Metro Area" suffix bug found earlier. `test_api.py`
      hits `/metros`, `/metros/{id}/series`, `/query/feedback` through
      FastAPI's TestClient against a synthetic fixture db - never the
      real `athena.db`. `POST /query` itself is deliberately excluded -
      that's the eval suite's job, since it needs a live DeepSeek call.
- [x] **Frontend test suite** (Vitest + React Testing Library, 26 tests):
      `format.ts` and `analysis.ts` (pure functions) plus component tests
      for `MetroGrid` (badge logic), `InterpretationPanel` (the
      transparency panel's actual rendered output), and `QueryResults`'
      empty-state path. Chart rendering (Recharts) is intentionally left
      to the existing real-browser Playwright checks - jsdom doesn't
      implement the layout/ResizeObserver behavior Recharts needs.
- [x] **Real bug found immediately, not a metaphor for why testing
      matters:** the very first frontend test run caught a genuine
      timezone bug in `analysis.ts`. Period strings like `"2024-02-01"`
      parse as UTC midnight; the peak/trough month formatter rendered in
      the browser's *local* timezone with no `timeZone` pin, which for
      anyone west of UTC (all of the US) pushes the 1st of the month back
      into the previous day - every "peaked in Feb 2024" callout was
      silently naming the wrong month. Fixed by pinning the formatter to
      `timeZone: "UTC"`. This had been live and unnoticed since the
      result-analysis feature shipped in Phase 2.
- [x] **CI** (`.github/workflows/ci.yml`, GitHub Actions): pytest and the
      frontend suite + `tsc -b` run on every push to `main` and every PR.
      Deliberately does **not** include the DeepSeek-backed eval suite -
      that costs real API money per run, and Johan wants the project in
      "demo mode" (near-zero ongoing cost) while applying for jobs. The
      eval suite instead runs manually, about twice a week, per his
      explicit instruction - a deviation from this phase's original plan
      ("run the eval set on every push"), made deliberately, not by
      default.

## Phase 5 — Deployment
- [x] **Live**, 2026-10-09: a second Oracle Cloud Always Free VM
      (`athena-realestate-vm`, separate from Apollo Shell's box, same
      VCN), Oracle Linux 9. Backend runs as a systemd service (gunicorn +
      `uvicorn.workers.UvicornWorker`, auto-restart), reverse-proxied by
      nginx; frontend is a static Vite build served by nginx directly -
      no Python process for it, matching the original plan. Real domain
      (`athenarealestate.app` / `api.athenarealestate.app` via Porkbun),
      TLS via Certbot/Let's Encrypt on all three names with auto-renewal,
      HTTP->HTTPS redirect. `.env` and the already-ingested `athena.db`
      copied via `scp`, never through git, mirroring Apollo's established
      pattern. Two real SELinux bugs hit and fixed along the way,
      specific to Oracle Linux's enforcing policy, not config mistakes:
      systemd couldn't execute the venv's own binaries (labeled as
      home-directory content; fixed with a persistent `semanage
      fcontext` rule so it survives future `pip install`s) and nginx
      couldn't proxy to the backend (`httpd_can_network_connect` is off
      by default; enabled it). VM creation itself was gated for days on
      Oracle's Always Free A1 capacity shortage in the Ashburn region,
      not resolved by any configuration change - an unattended retry
      script (`oci compute instance launch`, cycling all three
      availability domains every ~5 minutes) running on the Apollo VM
      eventually succeeded.
- [x] **Real CD**, `.github/workflows/deploy.yml`: a `workflow_dispatch`
      GitHub Actions deploy, mirroring Apollo's exactly (manual trigger
      only, SSH in, pull, re-run tests server-side, restart, verify) -
      extended with the one real adaptation Apollo doesn't need: Athena's
      frontend is a separate static build, so the workflow also runs
      `npm run build` on the server and redeploys `/var/www/athenarealestate`
      before restarting the backend. The exact sequence was run by hand
      once first and confirmed working end-to-end against the live site
      (including a real "why" HUD commentary query against
      `api.athenarealestate.app`) before being written into the workflow
      file - not written and trusted blind. Node 22 added to the VM for
      this (one-time setup, same category as git/Python/nginx/certbot
      earlier); `npm` needed a manual `/usr/bin/npm` wrapper script after
      installing via `dnf module` - its own package didn't symlink one in,
      a real, minor Oracle Linux packaging quirk, not a config mistake.

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

## Phase 8 — Retrieval-augmented market commentary
Backend, frontend, and deploy all real-data-verified. Motivated by
wanting genuine RAG experience for the forward-deployed AI engineer
angle, not by wanting RAG for its own sake.

- [x] **Coverage checked by hand, the real blocker from the original plan
      below.** HUD's CHMA listing pages are bot-gated the same as
      Redfin/BLS (confirmed directly - automated fetches get an empty,
      gated response), so this meant a real browser check across 5
      states (CA, TX, FL, OH, RI), not an automated scrape. Result: 23 of
      50 tracked metros have a verified, downloaded report. Two honest
      exceptions, both deliberately included anyway rather than silently
      dropped, and both disclosed via `as_of_date` at query time rather
      than presented as current: `los-angeles-ca` (HUD's newest
      *full-metro* report is from 2013 - newer sub-area reports exist but
      only cover part of LA) and `providence-ri` (HUD publishes a
      statewide Rhode Island report, not a Providence-specific one). The
      remaining ~27 metros haven't been checked yet - growing this set is
      unstarted, manual work, not blocked on anything technical.
- [x] **A second tool, `search_market_commentary`, alongside
      `query_market_metrics`.** `tool_choice` changed from forced-single-
      function to `"required"` - the model must call a tool, but
      genuinely picks which one. Verified directly against the real
      DeepSeek API, not just unit-tested: "why is rent falling in Austin"
      correctly triggered the commentary tool with real, relevant cited
      text; "what is the median sale price in Denver" correctly stayed on
      `query_market_metrics`, 176 real results, no regression.
- [x] **Strictly separated from the structured answer, never blended** -
      same honesty principle as the `median_gross_rent` fallback
      (`approximated_metros`). `MarketQueryResponse.filters` is `null`
      for a commentary response; `commentary` is `null` for a metrics
      response - never both populated, never guessed at from one shape.
- [x] **PDF extraction and chunking**, one `MarketCommentaryChunk` row
      per PDF page (these reports are already organized into named
      sections that map one-to-one onto pages). Real complication hit and
      handled, not glossed over: LA's 2013 report uses an older PDF
      template where kerning breaks some words apart in extraction (e.g.
      "ANAL YSIS") - the boilerplate-stripping logic was written to
      tolerate this rather than assuming one clean format for all 23
      files.
- [x] **Lightweight similarity search, not an embedding model** - a
      deliberate simplification from the original plan (below), decided
      with Johan before building: metro selection already narrows
      retrieval to one ~30-page document before ranking ever runs, so
      this is "which section of this one report," not open-domain
      search. TF-IDF (scikit-learn), computed fresh per query over one
      metro's handful of chunks, no precomputed vector index, no torch
      dependency on a small deployment VM. Swappable later if the
      quality bar ever demands it - the tool's interface (metro + topic
      in, ranked cited chunks out) doesn't change either way.
- [x] **Real source data kept out of git** - the 23 PDFs are 83MB and
      growing, versus ~20MB for everything else in `data/samples/`
      combined. Handled like `.env`/`athena.db`: `scp`'d directly,
      documented in `DOCUMENTATION.md`, not committed.
- [x] **Backend test coverage** for the deterministic retrieval logic
      (metro resolution, the no-coverage case, and a real test that
      ranking actually discriminates by topic rather than just returning
      the first few chunks) - `backend/tests/test_market_commentary.py`.
      `interpret_query`'s live tool-choice behavior stays out of pytest,
      same reasoning as `query_market_metrics` - that needs the eval
      suite, not a unit test.
- [x] **Frontend**: `QueryResults` renders a commentary response's
      sections and citation instead of a chart. Went through four real
      readability passes after Johan flagged the raw-text rendering as
      hard to read (distinct sections, no duplicated labels, real line
      width; then in-page subheadings and flagged mid-sentence starts;
      then the synthesized summary given its own loud, highlighted
      treatment instead of blending in as another caption; then the
      source excerpts demoted to a compact, numbered, footnote-scaled
      list - smaller type, flat instead of a raised card, no shadow -
      now that they're explicitly secondary to the summary above them).
- [x] **Reconstructed sentences across a page break, by sentence
      boundary, not just flagged.** The "…" flag (first attempt) was
      honest but didn't read as an answer. A first reconstruction attempt
      (second attempt) prepended the previous page's last PDF *line* -
      better, but a line wraps wherever the column width cuts it, not at
      a sentence boundary, so it could itself already be mid-sentence
      (real case: Austin p.31's last line was "the following 2 years was
      largely due to..." - itself a fragment, because the sentence's
      real start, "The subsequent increase from 7.9 to 10.2 percent
      during...", was a full line earlier on the same page). Fixed by
      tracking the previous page's last whole *paragraph* instead and
      splitting it on sentence-ending punctuation
      (`_trailing_sentence`), taking the real trailing sentence rather
      than an arbitrary line-wrap cut. Also handles a page ending on a
      chart/figure caption ("## Source: CoStar Group") by scanning
      backward past it to the last real paragraph, rather than treating
      that as a dead end. Verified against all 23 metros' real PDFs:
      671 total chunks, 0 ellipsis-prefixed.
- [x] **Synthesized, thesis-first answers, not raw PDF excerpts as the
      answer.** Even with page-level chunking and the "…" mid-sentence
      flag, a raw excerpt still doesn't read like an answer to the
      question asked - it reads like a quote grabbed out of context,
      because it is one. `synthesize_commentary_answer` makes a second,
      strictly-grounded DeepSeek call that turns the retrieved chunks
      into a direct answer in the model's own words (thesis first, then
      supporting detail) before they're shown as `explanation`; the raw
      chunks still render below for anyone checking the paraphrase
      against the source. Falls back to the old deterministic sentence
      if that second call itself fails, rather than failing the request.
- [x] Deployed to the live VM - the PDFs `scp`'d there manually (see
      `DOCUMENTATION.md` Deployment), not pulled by `git pull`.
- [x] **Eval suite cases for the tool-choice behavior** (2026-10-11): two
      cases (`commentary_why_rent_declining`, `commentary_why_population_growing`)
      now assert `interpret_query` actually routes to
      `search_market_commentary`, not just that the right metric/metro
      came back - a genuinely different outcome type (`CommentaryQuery`
      vs. `MarketQueryFilters`), checked by `isinstance` in
      `run_eval.py`. Still just two phrasings, not a wide range -
      growing this further, and the synthesized-answer's grounding,
      stays open.
- [ ] Grow coverage beyond the current 23 metros (same manual,
      bot-gated-browser process).
- **Deliberately considered and rejected: a live web-search tool
  instead of a pre-built corpus.** Technically possible (either a
  provider's hosted search tool, or a custom tool the same way
  `query_market_metrics` was built by hand) but rejected for this
  project specifically: live results aren't reproducible enough for the
  eval-suite-driven approach used everywhere else here, aren't
  vetted the way every other data source in this project has been, would
  hit the same live bot-gating unpredictably in production, and add real
  per-query cost/latency a pre-indexed corpus doesn't.

## Phase 9 — Real data pipeline (dbt + DuckDB + scheduled tests)

Portfolio-motivated, same reasoning as picking React/TS over Flask: the
goal is to be able to say "I run scheduled pipelines with tests," not
"I wrote ETL scripts." Everything so far (`ingest_market_data.py`) is a
one-time, by-hand process - fetch, parse with plain Python, `scp` the
resulting `athena.db` to prod once, never touched again by CI. This
phase adds a real ELT layer *alongside* that, not a rewrite of it: the
production FastAPI app keeps serving from the exact same SQLite file.

- [x] **Stage 1, live** (2026-10-31): a `pipeline/` dbt + DuckDB project,
      scheduled via `.github/workflows/pipeline.yml` (weekly cron +
      manual `workflow_dispatch`), covering two sources end-to-end -
      Redfin (simple reshape, proves the plumbing) and FEMA NRI (a real
      population-weighted aggregation, proves dbt is doing actual
      transformation work). dbt and DuckDB only ever run in the GitHub
      Actions runner, never installed on the production VM - it only
      ever receives a refreshed `athena.db` over `scp`, same
      scp-not-git convention the DB already used. `pipeline/scripts/
      publish_to_sqlite.py` does a scoped delete+insert (`source IN
      ('REDFIN', 'FEMA')` only) against the *downloaded* production
      file, never a fresh/empty one - every other source's rows, and
      the live `QueryUsage`/`QueryFeedback` tables, are never touched.
      Verified against the real data before shipping: dbt's build
      reproduces the exact same row counts and values (121,218 Redfin
      rows, 40 FEMA rows, byte-for-byte identical) as the Python ingest
      it replaces for these two sources.
- [x] **Data quality tests, not just schema checks**: dbt schema tests
      (`not_null`/`unique`/`relationships`/`accepted_values`) plus three
      custom singular tests - one asserting every raw Redfin region name
      resolves to a real metro (catches the exact silent-mismatch class
      of bug this project has hit before), one bounding the FEMA hazard
      score to NRI's documented 0-100 scale, and one regression test
      recreating the real avg-vs-weighted bug caught during Phase 3's
      FEMA NRI work - fails if the weighted and plain-average scores
      ever collapse to the same number for a metro with genuinely
      unequal county populations *and* genuinely different county risk
      scores (the first version of this test had a false positive on
      Riverside-CA, whose two counties happen to have very similar risk
      scores despite a large population gap - fixed by also requiring a
      meaningful score spread, not just a population spread).
- [ ] Migrate the remaining sources (Apartment List, Census income/
      commute/property-tax/population/rent-trend, BLS, FHFA, Freddie
      Mac PMMS) the same way, one at a time, each its own small PR.
      Sources needing real Python preprocessing (Census's interleaved
      Estimate/MOE CSV layout) will need a thin `pipeline/scripts/
      load_raw_sources.py` pre-pass to a clean flat file dbt can read as
      a source. HUD CHMA (a text/RAG corpus, not tabular metrics) stays
      out of dbt entirely, forever.

See `PRODUCT_REVIEW.md` for an honest read on where this currently stands
against these phases, and `DOCUMENTATION.md` for the technical reference.
