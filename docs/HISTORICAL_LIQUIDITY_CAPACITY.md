# Historical Liquidity / Capacity Robustness

Implementation 39 continues directly from the cost-sensitivity result of
Implementation 38.

The purpose is to answer a narrower question:

> If we rebalance the same long-only portfolios using the historical traded
> notional actually present in the verified daily corpus, what portfolio size
> could each rebalance support under transparent participation assumptions?

## Historical liquidity evidence

The input is the already pinned V24 daily member corpus:

- source commit:
  `883e680a2564e38f4c08a21bc88aa95b8f164036`
- artifact:
  `historical_member_prices_resolved_2020-07_2026-08.csv.gz`
- SHA256:
  `b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141`
- authority:
  `VALIDATED_DERIVED_MARKET_DATA`

This is Yahoo-derived historical Close/Volume with official ticker-lineage
resolution. It is useful research evidence but is not relabeled as official
Borsa daily volume.

For ticker `i` on signal date `t`:

`ADV63(i,t) = mean(Close * Volume) over the 63 trading observations ending t`

No forward volume enters the measure.

## Capacity formula

For a rebalance leg with portfolio weight change `|delta_w|`:

`PortfolioNotionalMax = ADV63 * participation_rate * execution_days / |delta_w|`

Signal-date portfolio capacity is the minimum across every non-zero buy and
sell leg. A missing ADV observation makes capacity unavailable for that signal
date; it is never neutral-filled.

## Pre-registered sensitivity grid

Participation rates:

- 1%
- 5%
- 10%

Execution windows:

- 1 trading day
- 3 trading days

These are diagnostic scenarios. Implementation 39 does **not** choose one as a
production setting.

The report also shows what fraction of signal dates could support illustrative
portfolio notionals of TRY 1m / 5m / 10m / 25m / 50m.

Those notionals are descriptive reference points, not a capital-allocation
decision.

## Portfolio state

Implementation 38 rules remain unchanged:

- exact 5-of-5 common sample;
- top 20% long-only;
- equal weight;
- fold boundary reset to cash;
- Implementation 35 purge / embargo;
- Implementation 37 train-only dynamic weights.

No liquidity cutoff, portfolio-size optimization, or champion promotion is
allowed in this implementation.
