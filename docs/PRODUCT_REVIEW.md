# Product Review

Honest self-assessment, not a status report dressed up as one. Updated as
the project moves - see `ROADMAP.md` for what's planned and `git log` for
what's actually landed since this was last written. Rewritten clean at
this update rather than patched again - the previous version had
accumulated enough resolved history to obscure what's actually still open.

**Last updated:** 2026-09-30 (visual redesign done, three AI-capability extensions shipped, a real multi-turn bug found/fixed/regression-tested, the eval caught a second real issue on re-run, Census income + a median-rent fallback + a computed rent-to-income metric shipped as a third independent data source, Phase 4 - engineering rigor - finally landed after seven deferrals, a real timezone bug found by the first frontend test ever run, a fourth data source - Freddie Mac's national mortgage rates - added with its own non-metro schema, a fifth - BLS unemployment via its registered API - unexpectedly closed a real gap this project had previously given up on, and a sixth - FHFA house prices via FRED - shipped with a real, meaningfully worse coverage gap than any prior source, surfaced and decided on with Johan before building rather than after)

## What this is being judged against

Two goals, both real: a genuinely useful market-trend tool, and a
portfolio piece for landing a forward-deployed AI engineer role. This
review holds the project to both, not just "does it run."

## Where it actually stands

- **Data** - real, not synthetic, now from six independent sources.
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
  gaps.
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
- **Eval set: 31 cases now, and it's still finding real distinctions, not
  just passing.** One case (Anaheim rent) flipped from a genuine
  `no_data` case to a genuine `approximated` one *because the underlying
  behavior actually changed* - the eval caught that correctly rather than
  needing a hand update to "just pass." A sibling case (Anaheim household
  income) deliberately stayed a `no_data` case, checking the two related
  features don't get conflated. Full suite: **31/31 cases, 73/73 checks**.
  The repeatability check on this run again reproduced the metric-choice
  non-determinism first seen several updates ago (2 different metrics
  across 5 runs) - still real, still not something a code fix should be
  expected to eliminate, since it's the model's judgment call, not a
  structural bug.
- **Frontend** - redesigned (industrial/hazard-signage direction, per
  `PREFERENCES.md`) and verified in a real browser at every step, not
  just typed correctly - a genuine readability bug (overlapping chart date
  labels) and a genuine UX gap (no way back from results to the metro
  grid) were both caught this way, not by assumption. This was the
  standing risk this document flagged repeatedly ("deprioritized again");
  it's resolved now, which matters as much as the fix itself given how
  many times it got pushed.
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
- **Automated tests now exist and run in CI** (Phase 4, closed out this
  session after seven deferrals - see below): 60 backend pytest tests
  (query logic, crosswalk invariants, ETL, API contracts) and 26 frontend
  Vitest tests, both wired into GitHub Actions on every push/PR. Worth
  saying plainly: the very first frontend test run found a real,
  previously-unnoticed bug (a timezone issue in `analysis.ts` that named
  the wrong month in every peak/trough callout for any US-timezone
  viewer, live since Phase 2) - direct evidence this wasn't
  rigor-for-its-own-sake.
- **No auth, no deployment.** Real user accounts, multi-tenancy, and
  payments are a stated, co-equal pillar of this project's purpose
  (Apollo Shell had none of this; see `ROADMAP.md`'s top section and
  Phase 7), not a nice-to-have. Zero progress on it is a real gap against
  the project's own stated goals, not just a limitation to disclose. This
  is now the largest remaining gap - see below.

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

**Phase 4 is closed out** (this update) - the pattern named here across
the last seven updates (engineering rigor deprioritized behind every new
feature) finally broke. Worth being just as honest about the resolution
as the previous versions of this document were about the pattern: it took
seven deferrals and an explicit ask from Johan ("I like tests... so what
is phase 4 exactly?") to get here, not proactive prioritization. That's
still worth naming, not smoothing over.

The risk that replaces it: **Phase 7 (real user accounts, multi-tenancy,
payments) has zero progress**, and it's a stated co-equal pillar of this
project's purpose, not an optional add-on - the whole point of choosing
this over Apollo Shell again was to demonstrate real SaaS patterns Apollo
Shell never had. Six things have now shipped ahead of it (real data, the
NL layer, the visual redesign, three feature rounds, a third data source,
and now Phase 4) with legitimate reasons each time - but the same
pattern-recognition problem applies here as it did to testing: at some
point the reasons for going elsewhere first stop being sequencing
decisions and start being the actual answer to "why no accounts."

## Recommendation

Phase 7 should be the next thing seriously scoped, before another feature
round extends the same pattern that just took seven updates to break on
the testing side. Not necessarily built immediately - the roadmap's own
Phase 5 (deployment) arguably needs to exist first, since real payments
without a deployed target is a strange order of operations - but at least
scoped and sequenced deliberately, rather than deferred by default the
way tests were.
