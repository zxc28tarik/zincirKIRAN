# BIST100 Membership Backcast 2019–2021 — Result

Implementation 42A passed its fail-closed reconstruction on GitHub Actions run
**37672793867**.

Artifact: **11504889140**  
Digest: `sha256:85982c2389abd21007360aac9af668e6680d5878b3e20bc13ec5012e6fe22a3c`

## Anchor

The runner downloaded the frozen Total Rasyo execution panel at commit
`883e680a2564e38f4c08a21bc88aa95b8f164036` and verified SHA256:

`a3b14014aa4d3ff16a082bc0dac64346b906f4b7720aeae5a8c449a2add314f2`

The 2021-08-02 XU100 anchor contained exactly **100 unique names**.

## Event chain

The reconstruction uses **13 events**:

- 10 Borsa İstanbul periodic BIST100 constituent changes;
- 3 explicit intra-period events.

The intra-period events are essential:

- 2020-05-21: ADANA → SARKY;
- 2020-09-02: GUSGR → TURSG;
- 2021-06-16: BAGFS → ECZYT.

Removing any of these breaks event preconditions or historical membership
continuity.

## Fail-closed result

Every reverse checkpoint remained exactly **100 unique constituents**.

Earliest reconstructed state, before the 2019Q2 periodic event:

- member count: **100**
- member-set SHA256:
  `76f260abb7818f2fb2e04e505761f86ade3454a116d8ba93d6081fd37133de46`

The runner then replayed all 13 events forward.

Final member-set SHA256:

`b5173b92add41be91933a32410b32c7f8f078ab4a908be3a5c9e60793a43549e`

Anchor member-set SHA256:

`b5173b92add41be91933a32410b32c7f8f078ab4a908be3a5c9e60793a43549e`

Result:

**EXACT ANCHOR MATCH = TRUE**

So the event chain round-trips exactly.

## What this closes

We no longer need to infer 2019–2021 BIST100 history from today's constituents.
A deterministic, auditable event-chain reconstruction now exists.

This materially improves the survivorship-bias foundation for longer historical
research.

## What this does not close

Parent issue #104 remains open.

The current validated daily stock-price corpus begins in **2020-07**. A 52-week
high factor itself needs roughly 252 prior trading observations, which is why
membership evidence alone cannot create new independent H252 folds.

The next required step is therefore to audit/acquire earlier daily price history
for the reconstructed historical member set, followed by sector/fundamental
coverage checks.

No factor, model, cost, liquidity, or portfolio parameter changed in this
implementation.
