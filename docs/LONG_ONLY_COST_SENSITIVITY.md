# Long-Only Turnover / Cost-Sensitivity Diagnostic

Implementation 38 is the portfolio/cost-aware continuation explicitly left by
Implementation 37.

It compares the current benchmark champion and two composite challengers:

- `HIGH_52W_PROXIMITY`
- `EW5_COMPOSITE`
- `TRAIN_ONLY_EVIDENCE_WEIGHTED_5F`

## Pre-registered portfolio diagnostic

For every eligible validation signal date and horizon:

1. use the exact 5-of-5 common panel from Implementations 36–37;
2. preserve Implementation 35's matured-label purge and validation embargo;
3. estimate dynamic weights only from matured training dates;
4. rank the cross-section by the contender score;
5. hold the top 20% long-only, equal-weight;
6. reset to cash at each validation-fold boundary;
7. calculate actual weight-change turnover between consecutive validation
   signal dates inside the fold.

Gross turnover is:

`sum_i |w_new_i - w_old_i|`

The first portfolio in every fold therefore pays the full cash-to-portfolio
turnover. Fold resets deliberately prevent one validation fold from carrying
state into another.

## Cost sensitivity, not fabricated execution history

The repository does not currently contain authoritative historical bid/ask,
slippage, and market-impact observations for this panel. Implementation 38
therefore **does not invent them**.

Instead, it reports transparent all-in trading-cost scenarios of:

- 10 bps
- 25 bps
- 50 bps

per unit of traded notional.

For each signal date:

`net_forward_excess_proxy = gross_forward_excess_proxy - gross_turnover * cost_bps / 10000`

These are sensitivity scenarios, not observed historical transaction costs.

## Interpretation boundary

The H20/H60/H120/H252 targets remain the existing market-relative forward
return diagnostics. Because longer-horizon labels overlap while signals are
monthly, this implementation is **not** presented as a self-financing NAV
backtest.

Its purpose is narrower: test whether the long leg remains economically
interesting after the contender's own rebalance turnover is charged.

No portfolio-stock-count optimization, liquidity-cutoff optimization,
champion promotion, or production promotion is authorized.
