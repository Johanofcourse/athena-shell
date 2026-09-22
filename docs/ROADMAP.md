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
- [ ] Wire a real `DEEPSEEK_API_KEY` and run `/query` end to end
- [ ] Build an eval set: ~15-20 representative NL queries with expected
      filter output, scored automatically on every change
- [ ] Handle queries the schema can't answer (e.g. "near good schools" -
      no schools data) by degrading gracefully, not hallucinating a filter
- [ ] Decide the fallback story for ambiguous/ malformed model output

## Phase 2 — Visual redesign
- [ ] Replace the current generic/flat UI with the industrial,
      hazard-signage-inspired direction from `PREFERENCES.md`

## Phase 3 — Real data (or a defensible reason not to)
- [ ] Either swap in a real listings data source, or explicitly document
      why synthetic data is the right call for this project long-term

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
