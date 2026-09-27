# Product Review

Honest self-assessment, not a status report dressed up as one. Updated as
the project moves - see `ROADMAP.md` for what's planned and `git log` for
what's actually landed since this was last written.

**Last updated:** 2026-09-27 (real market schema + ETL built and verified, on top of the data sourcing and first live DeepSeek run from earlier the same day)

## What this is being judged against

Two goals, both real: a genuinely useful listing-history search tool, and
a portfolio piece for landing a forward-deployed AI engineer role. This
review holds the project to both, not just "does it run."

## Where it actually stands

- **Data model / API** - solid. Verified end-to-end against real seeded
  data (curl'd endpoints, exercised the filter->SQL path directly with
  real filter combinations, correct results).
- **NL query layer** - now verified live against DeepSeek, and it wasn't
  a clean first try, which is itself worth having on record: the model
  name was stale (`deepseek-chat` didn't exist under that name anymore),
  and `deepseek-flash`'s default "thinking" mode flatly rejects forced
  `tool_choice` - a 400 error DeepSeek's own docs don't document the fix
  for. Fixed by testing directly against the API rather than more doc
  reading. Five manual test queries post-fix all parsed into sane,
  correct filters (price thresholds, property type inference, sort
  clauses, relist counts). Tool-calling itself is reliable.
- **But "not hallucinating" isn't the same as "being honest."** One test
  query ("houses near good schools") proved this concretely: the model
  correctly avoided inventing a fake schools filter, but it also silently
  dropped that part of the request and returned unfiltered results with
  no indication school quality wasn't evaluated. A user could easily read
  25 results back as "these are near good schools." This is a real gap,
  not a hypothetical one - see `ROADMAP.md` Phase 1.
- **No eval set exists yet.** Five manual queries is a smoke test, not
  a measurement tool. Claiming the NL layer "works" without a repeatable
  way to score it isn't a credible claim in an FDAIE interview - building
  and reading evals *is* a large part of that job. This is now the
  highest-priority gap, above any UI work.
- **Frontend** - functional (grid, search, detail panel, price chart all
  render and work), but visually generic: rounded cards, soft blue
  accent, centered layout. This directly contradicts the project's own
  stated design bar (`PREFERENCES.md`), and a portfolio piece competing
  on distinctiveness shouldn't look like a templated SaaS dashboard.
- **Zero automated tests.** Fine for a fast prototype; undercuts the
  "engineering rigor" half of the pitch if it's still true by the time
  this gets shown to anyone.
- **Synthetic-only data** was the starting point; that's now actively
  changing (see below), so this bullet is closer to resolved than the
  others.

## Data sourcing (new since first draft)

The original assumption - scrape or search-engine our way to per-listing
price/relist history - doesn't survive scrutiny: no free source
backfills individual-listing history, and the sites that have it forbid
scraping (Craigslist v. PadMapper is directly on point - same product
idea, same outcome). Pivoted to real, free, legal **aggregate
market-trend data** (Redfin Data Center, Census ACS) instead of
per-listing data. This is a genuine product scope change - "any
address's history" becomes "how a market/segment is moving" - not a
finishing detail, and it was surfaced and agreed on explicitly rather
than assumed. Full writeup: `ROADMAP.md` Phase 3.

**Update:** both sides of the mission now have real, verified data - not
just sales. Redfin covers the sale side (50 metros, monthly, 2012-2026).
Apartment List covers the rent side (Rent Estimates, Vacancy Index, Time
on Market - up to 642 metros depending on the file, 2017/2019-2026). Both
spot-checked against known real-world market history and both check out
(Austin's rent-boom-then-bust story shows up consistently across price,
vacancy, and time-on-market independently). This is no longer a
hypothetical data strategy; it's real data sitting in `data/samples/`
waiting on a schema to load into - and a real crosswalk problem now that
two sources with different metro-naming conventions need to join. Still
blocked on the Census API key - see `ROADMAP.md` for the concrete next
actions and who owns them.

## Biggest risk to the job goal specifically

This has shifted, not disappeared. The core claim - "the AI layer works
reliably" - now has real (if thin) evidence behind it instead of zero.
The risk now is **proving it holds up**, not proving it exists: five
manual queries is not an eval, and the one real failure mode found so far
(silently dropping unsupported query aspects instead of flagging them)
is exactly the kind of thing that looks fine in a demo and falls apart
under real interview scrutiny. Everything else (data model, API, UI,
real data sourcing) is competent but not differentiating on its own; a
measured, honest account of where the NL layer works and where it
doesn't *is* the differentiator.

## Real data now has a schema (new since first draft)

`Metro` + `MarketMetric` tables built and loaded with all six real files
(50 metros, 121k+21k rows). Verified the same way as everything else in
this project so far - not "it ran without error," but "the exact numbers
match what was already validated from the raw files." That check caught
a real bug: one Apartment List file names metros differently than its
own other two files, and the mismatch silently produced zero rows for
that metric with no error - fixed only because the cross-check happened
at all. Worth remembering as a pattern: every data-join in this project
so far has had at least one non-obvious naming mismatch, and none of them
threw an error - they all failed silently. Assume the next one will too.

Added alongside the old `Listing`/`ListingEvent` model rather than
replacing it yet, so the already-verified DeepSeek integration keeps
working. The NL layer, API, and frontend still all point at the old
per-listing schema - that rewiring is the next real chunk of work, and
the eval set should wait for it rather than get built twice.

## Recommendation

Build the real eval set next (15-20 queries, expected filter output,
scored automatically) and use it to decide, deliberately, how unsupported
query aspects should be surfaced to the user - don't leave that as an
accidental side effect of whatever the model happens to do. That artifact
- not another UI pass, not the schema redesign - is what actually proves
the "AI engineer" half of the title.
