# InvestingPro Estimates / Revisions Acquisition

InvestingPro+ is no longer the primary source for data we already possess from the Total Rasyo evidence chain.

## What is already covered elsewhere

Zincir Kıran already has reusable evidence for:
- historical BIST100-member daily OHLC / adjusted close / volume;
- 60 x 100 monthly execution-price coverage;
- broad-sector/XU100 index closes;
- historical sector routing;
- 28 official KAP bulk financial archives;
- current KAP BIST roster and a large current share-basis sample.

Therefore InvestingPro should be focused on its genuinely additive data.

## Priority data families

1. **Analyst estimates**
   - EPS Estimate
   - Revenue Estimate
   - Forward EPS
   - Forward Revenue

2. **Analyst revisions**
   - EPS Revision / Estimate Change
   - Revenue Revision / Estimate Change
   - Analyst Count
   - Estimate Dispersion

3. **All-BIST expansion / cross-check**
   - current primary trading item universe
   - sector / industry
   - market cap / enterprise value
   - shares outstanding / free float
   - valuation and profitability snapshot metrics
   - BIST100-external names where historical market data is not yet bootstrapped

## Export limit

Investing.com's stock-screener help states that exports above 100 lines are not allowed by its data providers. Each screener batch must therefore contain **1–99 rows**.

Every export must record:
- exact filter description
- export timestamp
- row count
- SHA256 of the downloaded file
- authority class

## Authority classes

### CURRENT_SCREENER_SNAPSHOT

A current cross-sectional export. Useful for:
- current roster reconciliation
- all-BIST expansion
- current factor diagnostics
- Live Shadow

Not historical PIT.

### CURRENT_ESTIMATE_SNAPSHOT

Current analyst consensus/estimate values at export time.

Useful for current signals and future Live Shadow only. It must never be copied backward into historical dates.

### TIMESTAMPED_REVISION_HISTORY

Historical analyst estimate/revision observations are usable for PIT research only when each observation retains a timestamp showing when that revision/estimate was observable.

Historical usage is:
`observed_at <= cutoff_at`

If InvestingPro only shows the latest revision state without historical observation timestamps, the data remains current-only.

### FUNDAMENTAL_CROSSCHECK

InvestingPro historical/summary fundamentals used to compare against KAP and diagnose missing mappings. They do not override KAP publication/version authority.

## Reconciliation target

Current KAP bootstrap contains 807 roster rows. InvestingPro's union of <100-row export batches must be reconciled against this roster.

Required report:
- matched tickers
- KAP-only rows
- InvestingPro-only rows
- duplicate primary trading items
- issuer/ticker ambiguities
- missing metrics by ticker

No unmatched row is silently deleted.

## Prohibited target leakage

The following InvestingPro products are not training labels:
- Fair Value
- Health Score
- ProPicks AI
- ProTips score
- InvestingPro rating

Forward market-relative return remains the target.
