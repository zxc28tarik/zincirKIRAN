# First Equal-Weight Multi-Factor Challenger

The first composite challenger is deliberately simple and preregistered.

## Composite

Five sector-neutral factor scores:

- 52W High Proximity
- Low Volatility 63D
- 6-1 Momentum
- Operating Margin Acceleration
- Gross Margin Acceleration

Each factor receives exactly **20%** weight.

No train-fold fitting, horizon-specific weight, optimization or post-result
weight change is allowed in this implementation.

## Missingness

The primary composite requires all five factor scores for the same ticker and
signal date.

Missing factor values are not:
- filled with zero;
- treated as neutral;
- reweighted away.

## Fair comparison

The composite and every single-factor reference are evaluated on the exact
same 5-of-5 common sample.

Primary benchmark:
`HIGH_52W_PROXIMITY`

The walk-forward protocol is inherited unchanged from Implementation 35:
chronological expanding train, label-maturity purge, validation label-maturity
embargo and six-month validation blocks.

This is a challenger experiment only. It cannot automatically replace the
benchmark or authorize production.
