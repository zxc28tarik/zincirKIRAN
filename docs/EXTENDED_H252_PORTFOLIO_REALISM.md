# Extended H252 Portfolio Realism

Implementation 43 applies the already locked portfolio-realism stack to the
two-fold H252 evidence created in Implementation 42D.

Nothing is re-optimized.

## Contenders

- HIGH_52W_PROXIMITY
- EW5_COMPOSITE
- TRAIN_ONLY_EVIDENCE_WEIGHTED_5F
- FIXED_RIDGE_5F

## Portfolio protocol

The protocol is inherited unchanged from Implementations 38, 39 and 41:

- top 20% long-only;
- equal weight;
- reset to cash at each validation-fold boundary;
- turnover = sum absolute weight changes;
- 10 / 25 / 50 bps all-in cost sensitivity;
- dated ADV63 capacity;
- 1% / 5% / 10% participation;
- one / three execution days;
- illustrative TRY 1m / 5m / 10m / 25m / 50m notionals.

These remain sensitivity scenarios, not production settings.

## Sanity gate

Before opening extended results, the runner applies the same portfolio engine to
the original 60-month panel and requires the exact one-fold H252 metrics from
Implementation 41 to reproduce within 1e-12.

## Research question

Implementation 42D showed that the earlier ridge advantage did not replicate
when H252 moved from one evaluable fold to two.

Implementation 43 asks the investment version of that question:

> Does 52W High remain the stronger H252 long-only signal after turnover/costs,
> and does ridge remain rejected after execution realism?

No champion or production promotion is automatic.
