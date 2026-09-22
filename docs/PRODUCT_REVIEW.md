# Product Review

Honest self-assessment, not a status report dressed up as one. Updated as
the project moves - see `ROADMAP.md` for what's planned and `git log` for
what's actually landed since this was last written.

**Last updated:** 2026-09-22 (right after the initial scaffold, PR #1)

## What this is being judged against

Two goals, both real: a genuinely useful listing-history search tool, and
a portfolio piece for landing a forward-deployed AI engineer role. This
review holds the project to both, not just "does it run."

## Where it actually stands

- **Data model / API** - solid. Verified end-to-end against real seeded
  data (curl'd endpoints, exercised the filter->SQL path directly with
  real filter combinations, correct results).
- **NL query layer** - architecturally sound (tool-calling into a
  validated filter shape, not text-to-SQL), but **completely unverified
  in practice**. The DeepSeek call has never actually run - no API key
  was available while building it. For a project meant to demonstrate
  "I build reliable NL interfaces to data," an unexercised core feature
  is the single biggest risk on the board right now.
- **No eval set exists.** Claiming the NL layer "works" without a way to
  measure it isn't a credible claim in an FDAIE interview - building and
  reading evals *is* a large part of that job. This is the highest-
  priority gap, above any UI work.
- **Frontend** - functional (grid, search, detail panel, price chart all
  render and work), but visually generic: rounded cards, soft blue
  accent, centered layout. This directly contradicts the project's own
  stated design bar (`PREFERENCES.md`), and a portfolio piece competing
  on distinctiveness shouldn't look like a templated SaaS dashboard.
- **Zero automated tests.** Fine for a fast prototype; undercuts the
  "engineering rigor" half of the pitch if it's still true by the time
  this gets shown to anyone.
- **Synthetic-only data** is a defensible choice (no ToS/legal risk, full
  control over edge cases) - but be ready to say that out loud in an
  interview, because "is this real data" is an obvious first question.

## Biggest risk to the job goal specifically

FDAIE interviews probe two things above all else: does the AI layer
actually work reliably, and can you prove it, not just assert it. Right
now neither is demonstrated - the query layer is unexercised and there's
no eval. Everything else (data model, API, UI) is competent but not
differentiating on its own; the NL layer plus proof it works *is* the
differentiator, and it's currently the least finished part of the
project.

## Recommendation

Before more frontend polish: get a real `DEEPSEEK_API_KEY` in, run actual
queries through `/query`, and build a small eval set (15-20 NL queries
with expected filter output, scored automatically). That artifact - not
another UI pass - is what actually proves the "AI engineer" half of the
title.
