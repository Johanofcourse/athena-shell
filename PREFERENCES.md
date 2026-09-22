# Working preferences (carried over from Apollo Shell)

Context: Johan built Apollo Shell (a Florida utility-outage tracker) before
this project. These are the habits and preferences that worked well there -
worth keeping here too.

## Workflow
- PR merges stay manual - Johan clicks merge himself, not the assistant.
  Keeps him in the loop on what's actually shipping.
- Standard flow: new branch off main -> commit -> push -> open PR -> wait
  for Johan to merge -> verify it's actually live, don't just assume.
- Run the full test suite before every PR, not just spot checks.

## Verification habits
- Verify claims with real checks (curl a live endpoint, read actual
  logs/config, grep the real deployed .env) instead of assuming tests
  passing locally means production behaves the same way.
- After deploying anything that reads a new secret/env var, confirm it's
  actually present wherever it's running - don't just trust that tests
  passed. A real incident on Apollo Shell: a required env var was missing
  from the production .env and silently broke a feature until this kind of
  check caught it.

## Secrets
Never commit real secrets - .env only, gitignored from day one. Matters
even more here than on Apollo Shell, given real payment/auth credentials
(Stripe keys, session/JWT secrets) are coming.

## Communication style
- Itemized, categorized summaries after a test/audit sweep, not a raw
  dump - Johan uses these to actually learn the categories himself.
- Succinct docs - narrative prose is fine, but tight. Don't restate
  context he already has.
- When asked for a critical opinion (business decisions, monetization,
  "is this good enough"), give an honest, critical answer - don't default
  to validation.

## Consequential actions
Infra changes, deletions, anything hard to reverse - flag it and get a
quick confirmation first rather than doing it silently.

## Frontend / visual design preference
Not flat, generic, minimal dark-mode UI. Apollo Shell's explicit target
was a bold, industrial/hazard-signage-inspired look: stencil display type,
real texture and iconography instead of clean flat vector shapes - some
actual graphical realism and grit rather than the generic "AI-generated"
look (soft gradients, rounded-everything, safe sans-serif fonts, centered
hero sections). Ship rough-but-honest over polished-but-vague - it's fine
for something to look unfinished if it's telling the truth, but it should
never look like a templated SaaS dashboard.
