# Product Review

Honest self-assessment, not a status report dressed up as one. Updated as
the project moves - see `ROADMAP.md` for what's planned and `git log` for
what's actually landed since this was last written. Rewritten clean at
this update rather than patched again - the previous version had
accumulated enough resolved history to obscure what's actually still open.

**Last updated:** 2026-09-27 (full cutover to real data + verified NL layer + adversarial eval pass)

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
- **Eval set, now stress-tested, still 100%.** Expanded from 18 to 26
  cases specifically to try to break it: an off-topic request, a
  prompt-injection attempt, a typo, a self-contradictory ranking question,
  weird casing, a relative time range. All 26 passed. Read this
  carefully, not proudly: passing everything thrown at it could mean
  genuine robustness, or it could mean the adversarial cases weren't hard
  enough - given they all passed on the first attempt, the honest lean is
  toward the latter, not "case closed." One nuance worth keeping: the
  typo case passing is likely DeepSeek normalizing "Astin" -> "Austin"
  before our matcher (plain substring matching, not fuzzy) ever sees it -
  robustness from the LLM layer, not the code. A separate repeatability
  check (same ranking question, 5 runs) came back fully stable this time
  - that does **not** contradict the metric-choice variance observed
  earlier by hand (two different manual tests picked different metrics
  for the same question); it just means 5 samples didn't reproduce it.
  Non-determinism that shows up occasionally doesn't show up in every
  small sample, and a clean 5/5 isn't proof it's gone.
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
- **No auth, no deployment, no CI.** This bullet used to say "fine for
  local development" and leave it there - that undersold it. Real user
  accounts, multi-tenancy, and payments are a stated, co-equal pillar of
  this project's purpose (Apollo Shell had none of this; see
  `ROADMAP.md`'s top section and Phase 7), not a nice-to-have. Zero
  progress on it is a real gap against the project's own stated goals,
  not just a limitation to disclose.

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

Twenty-six hand-written cases that all pass, including the adversarial
ones, is still not proof of reliability - it's evidence that these
particular 26 attempts didn't find a failure. An interviewer who asks "how
do you know it's reliable" deserves "here's what I tried to break it with,
here's what I'd try next" as an answer, not a static perfect score
presented as a conclusion. The honest next step if this gets picked back
up is harder still: many more repeatability runs (5 wasn't enough to
resurface the variance already seen once by hand), and inputs that are
actually malformed rather than just adversarially phrased (empty-ish
strings, near the 300-char limit, non-English input).

Second risk, unchanged for a while now: the visual design still
contradicts the project's own stated bar. It kept getting correctly
deprioritized behind this work - that's now done, so this is next.

## Recommendation

The eval work has hit a reasonable stopping point for now: it's been
stress-tested once, honestly, and documented as "no failure found yet,"
not "solved." Move to the visual redesign next - it's been correctly
deferred multiple times, and there's no more data/AI-layer work left to
justify deferring it again right now.
