# Real Shadow Readiness / Production Evidence Inventory

Implementation 44 does not run a new alpha experiment.

Its purpose is to translate the real research chain completed through
Implementation 43 into a fail-closed inventory of what can support **prospective
shadow preparation** and what still blocks any production-readiness claim.

## Critical rule

Research Constitution §26 explicitly leaves exact production thresholds
unlocked. Therefore this implementation does **not** choose:

- minimum live IC;
- minimum live net return;
- drawdown threshold;
- minimum shadow-day count;
- production liquidity cutoff;
- production portfolio size.

Those values cannot be back-filled after seeing current research results.

## Classification

Every prerequisite is classified as one of:

- `VERIFIED_READY`
- `RESEARCH_ONLY`
- `MISSING`
- `BLOCKED`

A `RESEARCH_ONLY` item may support research diagnostics but cannot satisfy a
production authority claim.

## Expected fail-closed boundary

The repository already contains strong research engineering:

- historical-universe reconstruction;
- immutable price snapshots;
- real walk-forward / purge / embargo;
- long-leg validation;
- cost sensitivity;
- ADV capacity;
- replay/sanity receipts;
- champion/challenger tests.

But the following are known blockers before this inventory runs:

- historical financial version authority is incomplete;
- corporate-action detail is incomplete for full total-return authority;
- cost numbers are scenarios, not observed execution costs;
- no self-financing NAV/drawdown evidence exists for the current tournament;
- no prospective live shadow protocol/run/realized labels exist;
- production thresholds are intentionally not preregistered.

Accordingly, the strongest possible outcome is **protocol design ready**.
Historical shadow backfill and production eligibility remain forbidden.
