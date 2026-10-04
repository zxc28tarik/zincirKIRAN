# Experimental Factor-Lab Dataset Assembly

This is Zincir Kıran's first combined real-data research dataset contract.

## Input evidence

### Historical stock market corpus
- 271,267 resolved historical member rows
- OHLC / adjusted close / volume
- 2020-07 .. 2026-08
- validated derived market data

### Official market/sector index closes
- 7,415 rows
- XU100 / XUSIN / XUHIZ / XUMAL / XUTEK
- canonical PIT for the covered index scope

### Historical BIST100 sector routing
- 209 historical tickers
- 210 half-open sector routes
- 60 historical signal months
- 6,000 membership cells

### Semantic financial facts
- 5,052 reports
- 199,969 real KAP-derived semantic facts
- 5,633 / 6,000 historical cells contain own-period visible financial facts

## Authority

The combined dataset is **EXPERIMENTAL_VERSION_RISK** because the financial
side does not yet have exhaustive superseded-version enumeration.

Allowed:
- exploratory Factor Lab IC
- quantile analysis
- long-leg validation
- liquidity-tier robustness
- factor-definition debugging
- coverage analysis

Not allowed:
- production evidence
- Live Shadow historical backfill
- authoritative champion promotion
- claiming validated alpha

## Forward return labels

Labels come only from future market prices.

For H20 / H60 / H120 / H252:
1. find the signal date on the exact trading calendar;
2. move forward exactly N trading-calendar positions;
3. compute stock total-price return basis supplied by the research input;
4. compute market return over the same exact dates;
5. label = stock return - market return.

A horizon that has not matured or lacks required prices is **unavailable**.
It is never converted to zero or neutral.

Calendar-day approximations such as signal date + 20 calendar days are forbidden.

## Next operational step

Stage the pinned cross-project artifacts locally, parse the semantic facts into
the Zincir Kıran factor-field vocabulary, construct factor observations by
signal date, generate matured H20/H60/H120/H252 labels, then run Factor Lab.

The resulting metrics remain experimental until authoritative financial version
history replaces the experimental semantic input.
