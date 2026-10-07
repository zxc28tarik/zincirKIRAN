# Real Sector-Neutral / De-correlation Diagnostic

This diagnostic compares raw and broad-sector-neutral factor behavior on the
same historical BIST100 signal dates.

## Sector neutralization

Historical sector routes are point-in-time half-open intervals from the locked
M3 package.

Within each signal date and sector:

1. preserve the raw factor value;
2. normalize expected direction so higher means economically preferred;
3. require at least 5 usable securities in the sector;
4. convert values to within-sector percentile ranks;
5. subtract 0.5.

Missing routes, undersized sector groups and missing factor values remain
missing.

## Evaluation

For H20/H60/H120/H252, both raw and sector-neutral scores are evaluated against
the same future XU100-relative diagnostic return proxy.

The main question is whether the negative raw IC of ROA / operating
profitability survives broad-sector neutralization.

## Redundancy

For every factor pair, same-date overlap is aligned by ticker and Spearman
correlation is calculated when at least 20 observations exist.

The reported pair correlation is the mean of valid dated correlations.

Only |mean rho| >= 0.70 becomes a REDUNDANCY_CANDIDATE. This does not delete,
residualize or reweight either factor.

Authority remains EXPERIMENTAL_VERSION_RISK.
