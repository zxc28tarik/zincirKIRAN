# First Post-Activation Live Universe + Market Snapshot

Implementation 45C captures the first data artifacts that are genuinely
**prospective relative to Shadow v1 activation**.

Activation:

`2026-10-07T22:10:15Z`

This implementation still creates **no shadow run**.

## Universe

The current BIST100 snapshot is reconstructed from:

1. the frozen validated 2026-07 100-name BIST100 anchor;
2. the official Borsa İstanbul 2026Q4 periodic review effective 2026-10-01.

The Q4 event contains exactly 27 additions and 27 removals. Reconstruction is
fail-closed:

- every removal must be present in the July anchor;
- every addition must be absent before the event;
- output must contain exactly 100 unique tickers;
- the post-activation capture stores the official announcement bytes and SHA256.

Because the final snapshot is derived rather than a direct full official
constituent export, its 45B authority is conservatively
`VALIDATED_LIVE_RESEARCH`.

## Market

For the reconstructed 100-name universe, the capture stores the latest available
Yahoo raw Close and Volume with:

- `auto_adjust=false`
- no alias guessing
- explicit trade date
- explicit source symbol
- missing symbols rejected rather than filled.

Market authority is `VALIDATED_LIVE_RESEARCH`.

## Capture-once rule

The first successful workflow capture is committed as V1. Subsequent workflow
runs **must not refetch live vendor data**. They only verify committed hashes and
contract invariants.

Any future refresh becomes a new snapshot/version.

## Expected execution-gate result

Universe and market domains become post-activation evidence.

Real shadow execution remains blocked because 45A requires additional domains,
including corporate actions; composite tracks additionally require financial
and publication/revision authority.

No production threshold or broker action is introduced.
