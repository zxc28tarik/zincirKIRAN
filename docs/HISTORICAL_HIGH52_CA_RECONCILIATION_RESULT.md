# Historical 252-Day Corporate-Action Reconciliation — Result

Implementation 45E ran successfully on GitHub Actions run **37807488119**.

Artifact: **11563393415**  
Digest:
`sha256:4e15c3333aba8bd03881e1c67470642c2db6395ea75c9ee50cd1be3ab311c2db`

Frozen package commit:

`78c8dd7fb8b1771e7830be86cd5ebf584413c9a8`

## Exact lookbacks

45E did not approximate "one year."

For every current ticker with sufficient price history it selected the **latest
252 finite positive Adj Close observations** from the frozen 45D package.

- current tickers: **100**
- price-sufficient tickers: **99**
- earliest actual historical lookback start: **2025-10-13**
- frozen historical reconciliation end: **2026-07-31**

PAHOL remains separately blocked with only **224** usable observations.

## Historical KAP source

45E used the frozen W6 KAP inventory:

- source data commit:
  `d0c5ce25832dc94c138fc6141bba8fa8392cd00b`
- W6 audit provenance:
  `0c70e1607832624b1b90a9bf150271ab705a6036`
- manifest SHA256:
  `1935232295360b1026a036e725809e0e73a62253ce07145bbc1f13fd6abd1345`

Only **55** W6 response windows overlap the actual current 252-day intervals.
Those 55 frozen responses were fetched and individually verified against the
source manifest. The full 595-window archive was not unnecessarily copied.

## Historical CA result

The conservative existing Zincir Kıran corporate-action classifier found:

- **368** historical risk rows;
- affecting **98** current tickers.

This includes process/disclosure evidence such as dividends, capital changes,
bonus/rights issues, mergers/demergers and share-class risk.

A positive event is deliberately **not** treated as proof of an already-resolved
price adjustment. No ex-date, ratio, cash amount or payment date is invented.

## Combined current gate

| Status | Tickers |
| --- | ---: |
| HISTORICAL_CA_RISK_UNRESOLVED | **98** |
| RECENT_CA_RISK_UNRESOLVED | **1** |
| PRICE_HISTORY_INSUFFICIENT | **1** |
| FACTOR_INPUT_READY | **0** |

The special cases are:

- **PAHOL** — price-history insufficient, 224 observations.
- **TKFEN** — the only price-sufficient ticker with no historical classified
  risk in its exact lookback, but it still has **2 recent unresolved CA-risk
  disclosures** from the 45D Aug→current capture.

Therefore:

- factor-input-ready: **0**
- score computation allowed: **0**
- shadow signal allowed: **0**

## Interpretation

This is not a reason to weaken the classifier after seeing the result.

The event-absence screen was intentionally conservative. Its job was to prove
whether a ticker had a completely quiet adjustment window. The answer for the
current BIST100 is effectively **no**.

The next legitimate implementation is therefore **economic adjustment
resolution**:

- inspect the classified KAP event details;
- establish actual ex-date / effective date where authoritative evidence
  exists;
- establish split/bonus/rights/dividend adjustment details where available;
- determine whether the frozen Yahoo Adj Close series demonstrably reflects the
  event;
- keep unresolved events blocked.

Only that evidence can turn a classified process disclosure from
`UNRESOLVED` into a safe adjustment state.

45E computes no HIGH_52W score and creates no shadow run, order, production
threshold or champion promotion.
