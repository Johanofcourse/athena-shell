# Product Review

Honest self-assessment, not a status report dressed up as one. Updated as
the project moves - see `ROADMAP.md` for what's planned and `git log` for
what's actually landed since this was last written. Rewritten clean at
this update rather than patched again - the previous version had
accumulated enough resolved history to obscure what's actually still open.

**Last updated:** 2026-09-27 (full cutover to real data + verified NL layer + first real eval)

## What this is being judged against

Two goals, both real: a genuinely useful market-trend tool, and a
portfolio piece for landing a forward-deployed AI engineer role. This
review holds the project to both, not just "does it run."

## Where it actually stands

- **Data** - real, not synthetic. Redfin (50 metros, monthly sale-side
  data, 2012-2026) and Apartment List (rent/vacancy/time-on-market,
  2017/2019-2026), both independently spot-checked against known
  real-world market history (Austin's 2012 low, 2022 pandemic-boom peak,
  2023+ cooldown, and the matching rent/vacancy story) before being
  trusted. Getting here required abandoning the original plan (scrape or
  search-engine per-listing history - doesn't survive scrutiny, see
  `ROADMAP.md` Phase 3) and finding a legally clean alternative instead.
- **NL query layer** - verified live against DeepSeek, not just
  architected. Getting a working integration required two real,
  undocumented fixes (stale model name, a "thinking mode" incompatibility
  with forced tool-calling) found by testing directly against the API,
  not by reading more documentation.
- **Three honesty behaviors, deliberately built:** the model names parts
  of a question it can't answer instead of dropping them
  (`unsupported_aspects`); a metro with no data for a requested metric
  says so instead of returning nothing (`no_data_metros`); an unmatched
  metro name is surfaced, not swallowed (`unmatched_metros`). All three
  exist because manual testing found the failure mode first - not because
  they were anticipated up front.
- **A real eval set exists**: 18 cases, 44 checks, currently 100%. Read
  that number as "hasn't found a failure yet," not "is correct" - it's an
  18-case first pass that doesn't cover adversarial input or the
  metric-choice non-determinism already observed by hand (the same
  ranking question picked a different, still-defensible metric on
  different runs). A score that never moves again would itself be a
  reason to write harder cases.
- **Frontend** - fully rewired to the real data (metro browser, trend
  charts, ranking charts), verified in an actual browser (not just typed
  correctly) - zero console errors across the query flow. Still visually
  generic: rounded cards, blue accent, centered layout. This directly
  contradicts the project's own stated design bar (`PREFERENCES.md`), and
  hasn't moved since it was first flagged - it's been correctly
  deprioritized behind the data/AI work each time, but it's still true.
- **Zero automated tests** for general code correctness. The eval set
  tests NL-layer behavior specifically; it isn't a substitute for testing
  the ETL, the crosswalk, or the API contracts.
- **No auth, no deployment, no CI.** Fine for local development, not
  hidden - see `ROADMAP.md` Phases 4-5.

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

The eval set is real but thin. Eighteen hand-written cases that all pass
is a good start and a weak final claim - the honest read is "no known
failures yet," and an interviewer who asks "how do you know it's
reliable" deserves a better answer than a static 18/18. The next
highest-value work is adversarial and ambiguous cases that might actually
fail something, not more UI polish and not a bigger eval set for its own
sake.

Second risk, unchanged for a while now: the visual design still
contradicts the project's own stated bar. It keeps getting correctly
deprioritized, but "correctly deprioritized" three times in a row is
worth naming as a pattern, not just repeating the deferral.

## Recommendation

Before touching the frontend: try to break the eval. Write cases designed
to fail - ambiguous metric choices, conflicting instructions, queries that
mix a supported and unsupported aspect in ways the 18 current cases don't.
A number that only ever goes up because nothing hard was tried isn't
evidence of reliability. If it's still solid after that, *then* the visual
redesign is next in line.
