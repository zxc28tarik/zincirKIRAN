# First Post-Activation Live Universe + Market Snapshot — Result

Implementation 45C produced the first immutable data capture that is genuinely
prospective relative to Shadow v1.

Workflow: **37803743421**  
Artifact: **11561263797**  
Artifact digest:
`sha256:99f8afaf89ef1de17a4391b18b56a377519f05fa8f3b3312b4e157c1162aa76e`

Frozen package commit:

`cf1739b7c246ea9620152ae21892842da2aef716`

## Temporal boundary

Shadow v1 activation:

`2026-10-07T22:10:15Z`

Snapshot captured:

`2026-10-07T23:37:36.184902Z`

The snapshot is therefore strictly post-activation.

## Universe

The current 2026Q4 BIST100 reconstruction contains exactly **100 unique names**.

It combines:

- frozen validated July-2026 BIST100 anchor;
- official Borsa İstanbul Q4-2026 27-in / 27-out periodic event.

Frozen hashes:

- universe CSV:
  `4f32de18caaea7b4fe3f5b136f03aa810b5033510bbb59730dae3a47447761d9`
- official announcement raw bytes:
  `9dc2639d4c10d06b7668a2ff3348e0f6a591e4eff5711152c1d5af4ba304c0a1`

Authority remains conservatively **VALIDATED_LIVE_RESEARCH**, not an overstated
direct full-constituent official export.

## Market

The reconstructed 100-name universe was queried with pinned yfinance semantics:

- requested: **100**
- captured: **100**
- rejected: **0**
- observed trade date: **2026-10-06**
- auto-adjust: **false**

Frozen market gzip SHA256:

`7d878df6d07534ab4c5f08d737e2efb9f1450ede32c3a9f28c48317d3783aabc`

The snapshot contains raw Close and Volume. It is
`VALIDATED_LIVE_RESEARCH`, not official Borsa market truth.

## 45B execution gate

Available post-activation domains are now:

- UNIVERSE
- MARKET_PRICES
- VOLUME_LIQUIDITY

All four research tracks remain fail-closed:

- HIGH_52W_PROXIMITY → **FACTOR_UNAVAILABLE**
- EW5_COMPOSITE → **FACTOR_UNAVAILABLE**
- TRAIN_ONLY_EVIDENCE_WEIGHTED_5F → **FACTOR_UNAVAILABLE**
- FIXED_RIDGE_5F → **FACTOR_UNAVAILABLE**

For 52W High the immediate missing required domain is **CORPORATE_ACTIONS**.

Composite tracks additionally lack live FINANCIALS, PUBLICATION_REVISIONS and
SECTOR_ROUTES; dynamic/ridge also need their corresponding state snapshots.

This is the intended result. Having market data does not authorize a shadow
signal by itself.

## Decision

Implementation 45C successfully creates the first immutable post-activation
universe/market evidence set.

It does **not** create a shadow run, order, champion promotion or production
threshold.

The next narrow blocker for the simplest 52W track is a prospective
CORPORATE_ACTIONS live-domain snapshot.
