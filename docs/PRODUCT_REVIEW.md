# Product Review

Honest self-assessment, not a status report dressed up as one. Updated as
the project moves - see `ROADMAP.md` for what's planned and `git log` for
what's actually landed since this was last written. Rewritten clean at
this update rather than patched again - the previous version had
accumulated enough resolved history to obscure what's actually still open.

**Last updated:** 2026-10-11 (four new metrics shipped in one session -
commute time, property tax, and population from Census ACS, plus natural
hazard risk from FEMA's National Risk Index as a seventh independent data
source - each with its own real complication (an Austin CBSA-rename bug
that silently dropped 10 of 12 years of population history, a
population-weighted county-to-metro aggregation for hazard risk, an
Akamai 403 that only `curl` gets past). Also closed a real, previously-
flagged-and-deliberately-deferred bug: ranking queries ("which metros are
growing/rising fastest") were silently ranking by latest absolute value,
not rate of change - fixed with a genuine third `sort_by` mode across the
whole query system, verified live against the exact phrasing that exposed
it. Restructured the answer layout as an inverted pyramid (narrative ->
caveats -> source citation -> chart) per direct feedback, and added
source citations to metric queries for the first time. Fixed a mobile
layout bug (two stacked CSS `min-width: auto` defaults clipping the
Income column) - open as PR #79, not yet merged. Eval suite grew from 37
to 47 cases covering all of the above; backend/frontend test totals now
125/38. Previous update, 2026-10-09: Phase 5 - deployment - closed: live
at `athenarealestate.app` on a second Oracle Cloud VM, real TLS, two
genuine SELinux bugs hit and fixed rather than configured around; see
`ROADMAP.md` Phase 5 for the full technical account. Before that,
2026-09-30: visual redesign done, three AI-capability extensions
shipped, a real multi-turn bug found/fixed/regression-tested, the eval
caught a second real issue on re-run, Census income + a median-rent
fallback + a computed rent-to-income metric shipped as a third
independent data source, Phase 4 - engineering rigor - finally landed
after seven deferrals, a real timezone bug found by the first frontend
test ever run, a fourth data source - Freddie Mac's national mortgage
rates - added with its own non-metro schema, a fifth - BLS unemployment
via its registered API - unexpectedly closed a real gap this project had
previously given up on, a sixth - FHFA house prices via FRED - shipped
with a real, meaningfully worse coverage gap than any prior source,
surfaced and decided on with Johan before building rather than after,
and - after real viewer feedback that the original look read as
construction-site caution tape - a blue/red palette refresh plus a real
geographic metro map replacing the plain browsing grid)

## What this is being judged against

Two goals, both real: a genuinely useful market-trend tool, and a
portfolio piece for landing a forward-deployed AI engineer role. This
review holds the project to both, not just "does it run."

## Where it actually stands

- **Data** - real, not synthetic, now from seven independent sources.
  Redfin (50 metros, monthly sale-side data, 2012-2026) and Apartment
  List (rent/vacancy/time-on-market, 2017/2019-2026), both independently
  spot-checked against known real-world market history (Austin's 2012
  low, 2022 pandemic-boom peak, 2023+ cooldown, and the matching
  rent/vacancy story) before being trusted. Getting here required
  abandoning the original plan (scrape or search-engine per-listing
  history - doesn't survive scrutiny, see `ROADMAP.md` Phase 3) and
  finding a legally clean alternative instead. Census ACS (median
  household income, plus a county-level gross-rent fallback for the 10
  metro-division metros) joined as a third source, matched against its
  own distinct metro-naming convention - a third crosswalk entry, not a
  reuse of either existing one, since Census's own official boundary
  names drift across time independent of both Redfin's and Apartment
  List's. Freddie Mac's mortgage rate history joined as a fourth source
  this session, the first genuinely *national* one - deliberately not
  squeezed into the metro crosswalk pattern the other three share (see
  `NationalMetric` in `DOCUMENTATION.md`), since a national rate isn't a
  per-metro fact and forcing one would have been the same kind of
  quiet correctness compromise this project has refused to make
  elsewhere. BLS unemployment data joined as a fifth source the same
  night, via a real, registered API (`api.bls.gov`) rather than the
  bulk file that was bot-gated earlier in this project - and it turned
  up a genuine, pleasant surprise: unlike Apartment List and Census's
  income table, BLS actually publishes metropolitan divisions
  separately, so the same 10 gap metros that have never had real
  rent-side or income-side data got **real, non-approximated**
  unemployment numbers instead of a sixth thing to flag as missing.
  FHFA's house price index (via FRED) joined as a sixth source the same
  night, and this one cut the other way: a real coverage gap
  meaningfully worse than any other source (no combined index at all for
  Los Angeles, Chicago, San Francisco, Seattle, Washington DC, Miami,
  Philadelphia, Dallas, or Detroit) - surfaced and discussed with Johan
  *before* building it, not discovered and quietly worked around after.
  38/50 real metros, honestly labeled, no fudged substitutes for the 12
  gaps. FEMA's National Risk Index joined as a seventh source this
  session, for natural hazard risk - the one with the most genuine design
  work behind it, since NRI publishes at county level and getting one
  number per metro meant a deliberate population-weighted aggregation (a
  simple average would let a sparsely-populated outlying county pull a
  metro's score around as much as its dense urban core), not a reused
  crosswalk pattern. Three more Census ACS pulls (commute time, property
  tax, total population) joined the same session, reusing the existing
  income crosswalk - population is the only one of the three that's a
  real multi-year trend, and ingesting it caught a real bug first: OMB
  renamed Austin's CBSA three times across 2012-2024, and a first,
  name-matching version of the ingest silently dropped 10 of Austin's 12
  years, producing a genuinely wrong "grew modestly" narrative. Fixed by
  matching on the CBSA's stable numeric code instead of its name.
- **NL query layer** - verified live against DeepSeek, not just
  architected. Getting a working integration required two real,
  undocumented fixes (stale model name, a "thinking mode" incompatibility
  with forced tool-calling) found by testing directly against the API,
  not by reading more documentation.
- **Four honesty behaviors, deliberately built:** the model names parts
  of a question it can't answer instead of dropping them
  (`unsupported_aspects`); a metro with no data for a requested metric
  says so instead of returning nothing (`no_data_metros`); an unmatched
  metro name is surfaced, not swallowed (`unmatched_metros`); and, new
  this session, a `median_rent` request answered with the Census
  fallback instead of real Apartment List data is explicitly flagged
  (`approximated_metros`), never silently presented as the same measure.
  All four exist because manual testing (or, for the fourth, a known
  geography gap from Phase 3) found the case first - not because they
  were anticipated up front.
- **A computed metric that combines two real sources honestly.**
  `rent_to_income_pct` = (median rent x 12) / median household income.
  The temptation with a derived metric is to let it paper over a missing
  input - it doesn't: the 10 metros missing Census income entirely still
  come back as `no_data_metros` for this metric even where the rent
  fallback above would otherwise have data, rather than silently omitting
  the income term or guessing at it.
- **A real ranking-correctness bug, flagged and deliberately left open,
  now actually fixed.** "Which metros are growing/rising fastest" used
  to silently rank by latest absolute value, not rate of change, because
  that was the only ranking mode that existed - found while building
  `total_population`, confirmed not population-specific (`median_rent`
  had the identical problem), and deliberately scoped out of that PR as
  too large a change to bundle in. Fixed this session with a genuine
  third `sort_by` mode (`"change"`) threaded through the query engine,
  both narrative-grounding functions, and the ranking chart's
  formatting - not a point patch, the scope the original finding called
  for. Verified against the exact phrasings that exposed the bug, live,
  with a Playwright screenshot confirming the chart renders percent
  values, not the metric's native unit.
- **Eval set: 47 cases now, and it's still finding real distinctions, not
  just passing.** One case (Anaheim rent) flipped from a genuine
  `no_data` case to a genuine `approximated` one *because the underlying
  behavior actually changed* - the eval caught that correctly rather than
  needing a hand update to "just pass." A sibling case (Anaheim household
  income) deliberately stayed a `no_data` case, checking the two related
  features don't get conflated. This update added 10 more: one per new
  metric's single-metro and ranking/compare phrasing, three for the
  `sort_by: "change"` fix (two for the exact phrasings that exposed the
  original bug, one confirming a single-snapshot metric still correctly
  resolves to `"value"` instead), and the suite's first cases that check
  *tool choice itself* rather than filter correctness - two "why"
  questions now assert `interpret_query` actually routes to
  `search_market_commentary` (a `CommentaryQuery`), not just that the
  right metro came back. Full suite: **46/47 cases, 117/118 checks** - the
  one failure is `adversarial_relative_time`, a pre-existing, deliberately
  adversarial case ("5 years ago") unrelated to this session's work and
  already documented as one that may legitimately fail. The repeatability
  check on this run again reproduced the metric-choice non-determinism
  first seen several updates ago - still real, still not something a code
  fix should be expected to eliminate, since it's the model's judgment
  call, not a structural bug.
- **Frontend** - redesigned (industrial/hazard-signage direction, per
  `PREFERENCES.md`) and verified in a real browser at every step, not
  just typed correctly - a genuine readability bug (overlapping chart date
  labels) and a genuine UX gap (no way back from results to the metro
  grid) were both caught this way, not by assumption. This was the
  standing risk this document flagged repeatedly ("deprioritized again");
  it's resolved now, which matters as much as the fix itself given how
  many times it got pushed. Restructured this session into a genuine
  inverted-pyramid layout (thesis first, chart last) with real source
  citations on metric queries for the first time, both per direct
  feedback rather than internal judgment call. A mobile layout bug
  (the Income column clipped on the 50-metro list, root-caused to two
  independent, stacked instances of the same CSS `min-width: auto`
  default) is fixed and verified but open as PR #79, not yet merged.
- **Three AI-capability extensions, all verified live**: a transparency
  panel exposing the exact tool-call arguments DeepSeek produced (the
  audit story this whole architecture was built around, made visible
  instead of just true in principle); a feedback widget logging real
  usage toward future eval growth; and multi-turn conversation support,
  confirmed to both carry context forward and correctly override it when
  asked. Building the third one is what found the bug and the eval
  finding described above - not a coincidence. Harder features surface
  more real problems, which is the point of building them before a
  portfolio review does it for you.
- **Automated tests now exist and run in CI** (Phase 4, closed out a
  previous session after seven deferrals - see below): 125 backend pytest
  tests (query logic, crosswalk invariants, ETL, API contracts) and 38
  frontend Vitest tests as of this update, up from 60/26 at Phase 4's
  close - grown steadily alongside every feature since, not left static.
  Both wired into GitHub Actions on every push/PR. Worth
  saying plainly: the very first frontend test run found a real,
  previously-unnoticed bug (a timezone issue in `analysis.ts` that named
  the wrong month in every peak/trough callout for any US-timezone
  viewer, live since Phase 2) - direct evidence this wasn't
  rigor-for-its-own-sake.
- **Deployment is now real; auth still isn't.** Phase 5 closed this
  update - the app is live at `athenarealestate.app` on a second Oracle
  Cloud VM, with real TLS, not a localhost-only demo anymore. But real
  user accounts, multi-tenancy, and payments (Phase 7) are a stated,
  co-equal pillar of this project's purpose (Apollo Shell had none of
  this; see `ROADMAP.md`'s top section), not a nice-to-have, and zero
  progress has been made on it. Deploying first without accounts means
  every endpoint is now open to the public internet rather than just
  local - a real, not hypothetical, gap. This is now the largest
  remaining gap - see below.

## What actually derisked this project, in order

1. Catching that the original data plan (scrape/search) was illegal or
   infeasible *before* building anything on top of it.
2. Verifying every claim with a real check instead of assuming - live API
   calls, real browser tests, exact-value cross-checks against raw data.
   This caught two real, silent bugs that "it ran without error" would
   have missed entirely: a naming mismatch that zeroed out one metric with
   no error, and (earlier) the same class of problem in the NL layer
   itself.
3. Treating "the model didn't hallucinate" as necessary but not
   sufficient, and building the honesty behaviors that follow from that.

None of these were UI work. That's not an accident - this project's
strongest evidence for "forward-deployed AI engineer" is the sequence
above, not any single screen.

## Biggest risk to the job goal specifically

**Phase 7 (real user accounts, multi-tenancy, payments) still has zero
progress**, and it's a stated co-equal pillar of this project's purpose,
not an optional add-on - the whole point of choosing this over Apollo
Shell again was to demonstrate real SaaS patterns Apollo Shell never had.
Phase 4 (engineering rigor) and Phase 5 (deployment) both closed out in
the updates before this one, which was real progress - but this update
added yet another full round on top (four new metrics, a real
ranking-correctness fix, a layout restructure, a mobile bug fix) with the
same legitimate-reason-each-time pattern this document named on the
testing side for seven straight updates before it finally broke. The app
has been live on the public internet, with zero auth, for two days now -
that's no longer a hypothetical gap. At some point the reasons for going
elsewhere first stop being sequencing decisions and start being the
actual answer to "why no accounts," and this project is closer to that
point than it was at the last update, not further from it.

## Recommendation

Phase 7 should be the next thing seriously scoped, before another feature
round extends the same pattern that just took seven updates to break on
the testing side. The sequencing argument that used to justify waiting -
"deployment should exist before payments, since real payments without a
deployed target is a strange order of operations" - no longer applies:
Phase 5 is done, the app is live. That removes the last legitimate reason
to keep deferring Phase 7 by default.
