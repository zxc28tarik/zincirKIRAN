# Historical 252-Day Corporate-Action Reconciliation

Implementation 45E applies the frozen W6 KAP inventory to the **exact** current
52W lookback windows derived from Implementation 45D.

## Source authority

Historical corporate-action evidence is pinned directly to the W6 audit commit:

`0c70e1607832624b1b90a9bf150271ab705a6036`

and manifest LF-canonical SHA256:

`1935232295360b1026a036e725809e0e73a62253ce07145bbc1f13fd6abd1345`

The W6 inventory proved:

- 2016-05-01 → 2026-07-31 coverage;
- 595 complete adaptive windows;
- zero failed windows;
- zero unsplittable 2,000-row cap hits.

45E does not refetch KAP history. It fetches only the frozen response bytes
already committed in that W6 source and verifies each response against the
frozen manifest hash.

## Exact 252-day window

For each ticker with sufficient 45D price history:

1. keep finite positive Adj Close observations;
2. take the **latest 252 observations**;
3. record the exact first and last trade date;
4. reconcile historical corporate-action evidence from the first observation
   through 2026-07-31.

No calendar approximation such as "one year" is used.

## Risk classification

The existing Zincir Kıran corporate-action classifier is reused. Historical
risk includes:

- capital increase/decrease processes;
- bonus/rights disclosures;
- merger/demerger;
- share-class changes;
- dividend-process disclosures.

A positive disclosure remains unresolved risk unless a later implementation
proves its economic adjustment details. No ex-date, ratio, amount, or payment
date is invented.

## Combined gate

Status precedence:

1. PRICE_HISTORY_INSUFFICIENT
2. HISTORICAL_CA_COVERAGE_INCOMPLETE
3. HISTORICAL_CA_RISK_UNRESOLVED
4. RECENT_CA_RISK_UNRESOLVED
5. FACTOR_INPUT_READY

A clean ticker may become `FACTOR_INPUT_READY` in 45E, but this implementation
still cannot emit a real shadow signal.
