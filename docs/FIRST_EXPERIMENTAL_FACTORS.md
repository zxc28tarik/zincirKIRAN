# First Experimental Factor Materialization

This implementation converts the first real-data Zincir Kıran research dataset into versioned candidate factors.

All outputs remain **EXPERIMENTAL_VERSION_RISK** until authoritative financial version history replaces the experimental semantic facts.

## Accounting discipline

KAP income/cash-flow semantic facts are YTD flows, not discrete-quarter values.

Rules:
1. First quarter YTD may represent that quarter directly.
2. Later quarter flow = current YTD - previous YTD only when:
   - canonical field matches;
   - fiscal period start matches;
   - previous period ends before current period.
3. TTM requires exactly four explicit quarter flows.
4. Instant balance-sheet values are not summed.
5. Average assets = (current assets + year-ago assets) / 2.
6. Missing inputs remain unavailable.
7. BANK / INSURANCE / FINANCIAL specialist sectors are not pushed through NONFIN formulas.

This prevents classic YTD leakage/double-counting such as summing 3M + 6M + 9M + FY YTD values.

## First financial candidates

| Factor | Family | Definition | Direction |
|---|---|---|---|
| Gross Profitability | Profitability | TTM Gross Profit / average assets | Higher better |
| ROA | Profitability | TTM Net Income / average assets | Higher better |
| Operating Profitability | Profitability | TTM Operating Profit / average assets | Higher better |
| CFO / Assets | Quality | TTM CFO / average assets | Higher better |
| Accruals | Quality | (TTM Net Income - TTM CFO) / average assets | Lower better |
| Asset Growth | Investment Discipline | Assets_t / Assets_t-4q - 1 | Lower better |
| Gross Margin | Profitability | TTM Gross Profit / TTM Revenue | Higher better |
| Gross Margin Acceleration | Fundamental Acceleration | Margin_t - Margin_t-4q | Higher better |
| Operating Margin | Profitability | TTM Operating Profit / TTM Revenue | Higher better |
| Operating Margin Acceleration | Fundamental Acceleration | Margin_t - Margin_t-4q | Higher better |
| CapEx / Assets | Investment Discipline | TTM CapEx / average assets | Lower better |

## First market candidates

| Factor | Family | Definition | Direction |
|---|---|---|---|
| Momentum 12-1 | Price Momentum | Close[t-21] / Close[t-252] - 1 | Higher better |
| Momentum 6-1 | Price Momentum | Close[t-21] / Close[t-126] - 1 | Higher better |
| 52-week-high proximity | Price Momentum | Current close / trailing-252 max close | Higher better |
| 63d realized volatility | Risk | sample std of 63 daily returns | Lower better |
| Amihud 63d | Liquidity | mean(|return| / (close × volume)) | Lower better |

Trading offsets are based on observed trading rows, not calendar-day approximations.

## Why Value is not in the first set

Reliable historical cross-sectional Value factors require a date-correct equity market capitalization / enterprise-value denominator.

The current experimental semantic corpus has issued capital and accounting values, but full historical share-state/corporate-action provenance is not yet sufficiently authoritative for all observations. Value will be added only after its denominator contract is closed rather than approximated from nominal capital.

## Factor Registry

All 16 definitions are registered as **CANDIDATE** hypotheses with:
- economic family
- economic concept key
- required input fields
- formula
- expected direction

No candidate is promoted merely because it can be computed.

## Next gate

After actual staged artifacts are parsed:
1. derive quarter and TTM facts;
2. materialize candidate values at each signal cutoff;
3. generate H20/H60/H120/H252 market-relative labels;
4. evaluate IC, ICIR, quantile monotonicity, long-leg, liquidity tiers and turnover;
5. retain the EXPERIMENTAL_VERSION_RISK label on every result.
