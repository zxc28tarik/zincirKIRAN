# Prospective 52W Input Sufficiency + Corporate-Action Risk Gate

Implementation 45D closes a semantic gap discovered before the first real
shadow run.

45C proves that a post-activation market **domain snapshot** exists. That does
not mean the 52W factor is numerically computable.

The research definition is:

`HIGH_52W_PROXIMITY = AdjClose_t / max(AdjClose over latest 252 observations)`

and requires exactly 252 finite positive adjusted-close observations.

## Price-history capture

The current 100-name 45C universe is captured again as a historical price
window, prospectively, after protocol activation.

The capture stores:

- raw Close;
- Adj Close;
- Volume;
- exact trade date;
- source symbol.

No alias guessing or neutral fill is allowed.

A ticker with fewer than 252 usable Adj Close observations is unavailable.

## Corporate-action gap

The previously frozen complete KAP inventory ends on 2026-07-31.

45D captures the official KAP disclosure stream from **2026-08-01 through the
capture date**, using the same proven market-wide `byCriteria` POST endpoint.

The endpoint's 2,000-row cap is handled exactly as in the validated historical
inventory:

- start with non-overlapping date windows;
- >=1900 rows causes bisection;
- a single day at the 2,000-row cap is not complete and fails closed;
- every request and response is content-addressed.

Only current-universe rows are materialized into the risk view.

## Conservative risk interpretation

The existing corporate-action subject/summary classifier is reused.

A positive process disclosure such as:

- capital increase/decrease;
- bonus/rights process;
- merger/demerger;
- dividend process;
- share-class change

does **not** automatically prove the economic adjustment is resolved.

If relevant adjustment detail is unavailable, that ticker is blocked.

## Historical portion of the 252-day window

Even a complete Aug-2026→current live gap does not by itself reconcile
corporate actions in the older part of the 252-observation window.

Therefore 45D records a separate:

`HISTORICAL_CA_RECONCILIATION_REQUIRED`

state until the frozen historical KAP inventory is reconciled for the actual
252-day lookback.

Implementation 45D cannot emit a shadow signal. Its job is to produce the
content-addressed evidence needed for that later decision.
