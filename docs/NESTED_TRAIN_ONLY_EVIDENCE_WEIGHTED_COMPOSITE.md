# Nested Train-Only Evidence-Weighted Composite

This challenger adapts factor weights inside each walk-forward fold without
using validation information.

For each horizon and fold:

1. build the fully matured, purged expanding train window;
2. calculate each factor's mean monthly Spearman IC using only train dates;
3. truncate negative train IC evidence to zero;
4. normalize the remaining positive evidence to sum to one;
5. if all train evidence is non-positive, emit NO SIGNAL for the fold.

Formula:

`w_i = max(train_mean_IC_i, 0) / sum_j max(train_mean_IC_j, 0)`

No cap, floor, smoothing constant, manually selected horizon weight, or
validation/test observation enters the weighting rule.

The factor universe is fixed before this run:
- 52W High Proximity
- Low Volatility 63D
- 6-1 Momentum
- Operating Margin Acceleration
- Gross Margin Acceleration

All five factors remain required for every scored row. Missing values are never
neutral-filled or partially reweighted.

The challenger is compared against:
- fixed equal-weight EW5;
- 52W High benchmark;

on the exact same 5-of-5 sample and embargoed validation folds.

This remains diagnostic / EXPERIMENTAL_VERSION_RISK evidence and cannot
automatically promote a champion or production model.
