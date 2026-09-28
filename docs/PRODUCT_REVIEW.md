# Product Review

Honest self-assessment, not a status report dressed up as one. Updated as
the project moves - see `ROADMAP.md` for what's planned and `git log` for
what's actually landed since this was last written. Rewritten clean at
this update rather than patched again - the previous version had
accumulated enough resolved history to obscure what's actually still open.

**Last updated:** 2026-09-28 (visual redesign done, three AI-capability extensions shipped, a real multi-turn bug found/fixed/regression-tested, and the eval caught a second real issue on re-run)

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
- **Eval set: 27 cases now, and it just proved its own point.** Expanded
  to 26 to try to break the first 100% (off-topic, prompt-injection, typo,
  self-contradiction, casing, relative time) - all 26 passed, and this
  review said plainly that a clean first pass was weak evidence, more
  likely to mean the cases weren't hard enough than that the system was
  robust. Building multi-turn support proved that literally: it surfaced
  a real bug (see below), and re-running the *same 26 cases* afterward
  produced a genuinely different result - `adversarial_off_topic` failed
  this time, then reproduced roughly 1-in-6 on repeated runs. Same test,
  different outcome, because the underlying behavior is probabilistic.
  That's not a regression to be alarmed by; it's the eval doing exactly
  what it's for. Fixed the same day: strengthened the system prompt to
  require `unsupported_aspects` even for fully off-topic questions,
  re-tested 10/10 clean (up from ~5/6), full suite now **27/27, 62/62**.
  The repeatability check on that same run reproduced the metric-choice
  variance previously seen only by hand - real and recurring, and a
  prompt fix wouldn't be expected to eliminate that the way the bed_size
  fix structurally did (that one was a code-level guardrail; this one is
  inherently the model's judgment call).
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

The largest single risk, and it's a pattern now, not a one-off: **engineering
rigor (Phase 4 - tests, CI) has been deprioritized behind every single
other thing for the entire project so far** - real data, the NL layer, the
visual redesign, three more features. Each individual deferral was
defensible. Six in a row is worth naming as a pattern rather than
re-litigating each time: at some point "there's always something more
valuable to build first" stops being a sequencing decision and starts
being the actual answer to "why no tests." An interviewer will notice the
pattern, not just the current excuse.

## Recommendation

Phase 4 needs to actually happen next, not be deferred a seventh time for
the next feature idea that comes up. The counter-argument ("one more
feature is more impressive") is exactly the reasoning that produced the
pattern above - and it's a weaker argument now than it's ever been, given
how much real AI-layer work already exists to point to.
