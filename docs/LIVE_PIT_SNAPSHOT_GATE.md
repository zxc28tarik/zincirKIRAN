# Live PIT Snapshot Contract & Shadow Execution Gate

Implementation 45B locks the **input boundary** for Prospective Shadow Protocol
v1. It still creates no real shadow run.

## Activation

45A activation is resolved from its merged main commit:

- commit: `1ae3ab623df58c8a22b7f943585f3d3835588e0a`
- activation_at: **2026-10-07T22:10:15Z**

Any candidate live snapshot captured at or before that timestamp is ineligible.

## Required live snapshot metadata

Every content-addressed live artifact carries:

- snapshot_id
- domain_id
- source_id / source_url
- logical_key
- source_available_at
- captured_at
- retrieved_at
- SHA256
- byte size
- authority

Temporal order is fail-closed:

`source_available_at <= captured_at <= retrieved_at <= executed_at`

and:

`activation_at < captured_at <= shadow_as_of`

## Authority classes

- AUTHORITATIVE_LIVE
- VALIDATED_LIVE_RESEARCH
- DISCOVERY_ONLY
- BLOCKED

DISCOVERY_ONLY and BLOCKED cannot satisfy a required track domain.

The gate converts missing or blocked live domains into the 45A abstention
semantics. It never neutral-fills a factor.

## Existing current-bootstrap artifacts

The September-2026 current KAP roster / share-state / raw-close package remains
useful as reference evidence, but it does **not** pass Shadow v1 execution:

- KAP roster is explicitly discovery-only, not a final investable universe;
- the package predates the 45A activation boundary;
- it does not carry the full 45B prospective timestamp contract;
- financial publication/revision and corporate-action live domains are not
  locked.

Thus the expected 45B outcome is:

- live snapshot contract: **READY**
- real shadow execution: **BLOCKED**
- historical backfill: **FORBIDDEN**

No shadow receipt or broker action is created.
