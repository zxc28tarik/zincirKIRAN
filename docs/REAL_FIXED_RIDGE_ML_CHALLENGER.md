# Real Fixed-Ridge ML Challenger

Implementation 40 is the first real-data ML challenger in Zincir Kıran.

It deliberately starts with a simple model rather than jumping directly to a
tree ensemble or neural network.

## Locked before results

Model:

`y = intercept + beta' * standardized_features`

with ridge penalty:

`lambda = 1.0`

The penalty is fixed before results. There is no search over lambda and no
validation tuning.

Features are the same five sector-neutral scores already used by EW5 and the
train-only dynamic composite:

- 52W High Proximity
- Low Volatility 63D
- 6-1 Momentum
- Operating Margin Acceleration
- Gross Margin Acceleration

All five remain required. Missing inputs are never neutral-filled.

## Leakage controls

For each horizon and walk-forward fold:

1. validation blocks come from Implementation 35;
2. every training signal's forward label must mature strictly before validation
   starts;
3. feature means and scales are estimated only from those matured train rows;
4. ridge coefficients are fitted only on train rows;
5. validation rows are scored with frozen train means/scales/coefficients.

No validation target or validation IC enters fitting.

## Comparison

`FIXED_RIDGE_5F` is compared on the exact same validation rows against:

- `HIGH_52W_PROXIMITY`
- `EW5_COMPOSITE`
- `TRAIN_ONLY_EVIDENCE_WEIGHTED_5F`

Metrics include fold IC, top-quintile forward excess proxy, Q5-Q1 spread, and
fold-level stability.

This is a challenger diagnostic only. It cannot promote itself to production.
