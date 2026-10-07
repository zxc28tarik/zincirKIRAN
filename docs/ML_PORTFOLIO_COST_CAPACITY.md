# ML Portfolio Cost + Capacity Tournament

Implementation 41 takes the fixed-ridge challenger from Implementation 40 and
subjects it to the exact portfolio realism layers already applied to the
interpretable contenders.

No new portfolio parameters are selected.

## Reused protocols

From Implementation 38:

- top 20% long-only;
- equal weight;
- fold boundary reset to cash;
- realized weight-change turnover;
- 10 / 25 / 50 bps all-in cost sensitivity.

From Implementation 39:

- dated 63-observation ADV from raw Close * Volume;
- exact verified daily market-data SHA;
- participation grid 1% / 5% / 10%;
- execution windows 1 / 3 trading days;
- capacity is the minimum binding rebalance leg;
- illustrative TRY 1m / 5m / 10m / 25m / 50m support.

From Implementation 40:

- fixed ridge lambda = 1.0;
- same five features;
- train-only standardization;
- matured training labels only;
- no hyperparameter tuning.

## Contenders

- 52W High Proximity
- EW5 Composite
- Train-Only Evidence-Weighted 5F
- Fixed Ridge 5F

The purpose is to test whether ML contributes **investable** evidence rather
than only rank IC.

No result can automatically promote a champion or production model.
