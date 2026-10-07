# Prospective Shadow Protocol v1

Implementation 45A preregisters the first **future-only** Zincir Kıran shadow
observation protocol.

It does not create a shadow run.

## Activation

The protocol has no invented activation timestamp in the PR.

Its activation rule is:

`FIRST_MAIN_MERGE_COMMIT_CONTAINING_THIS_PROTOCOL`

A future executor must resolve that merge commit timestamp as `activation_at`.

Every real shadow run must satisfy:

`as_of > activation_at`

Equality is rejected. Any earlier timestamp is rejected. Historical shadow
backfill is forbidden.

## Parallel research tracks

The shadow protocol records all current contenders in parallel:

- HIGH_52W_PROXIMITY
- EW5_COMPOSITE
- TRAIN_ONLY_EVIDENCE_WEIGHTED_5F
- FIXED_RIDGE_5F

for H20, H60, H120 and H252.

No track is promoted to a production champion by this protocol.

## Fail-closed sources

Each track declares required source domains. A required domain that is:

- blocked → `DATA_BLOCKED`
- missing/unavailable → `FACTOR_UNAVAILABLE`

It never becomes a neutral factor value.

Current Implementation 44 authority blockers therefore remain blockers in a
future executor until separate evidence closes them.

## Safety boundary

Shadow v1:

- creates no broker connection;
- creates no order;
- permits no production promotion;
- defines no production performance threshold;
- permits no retrospective shadow history.

Implementation 45B must separately lock the **live point-in-time snapshot path**
before any real shadow execution is allowed.
