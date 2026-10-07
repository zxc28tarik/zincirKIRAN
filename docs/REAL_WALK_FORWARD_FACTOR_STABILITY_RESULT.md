# Real Walk-Forward Factor Stability Result

This run uses chronological expanding-train evaluation with two leakage controls:

1. every training signal's forward label must fully mature before validation
   starts;
2. the next validation block begins only after the previous validation block's
   final forward label has matured.

So adjacent validation blocks cannot share unresolved forward-return windows.

## Sector-neutral OOS results

| Factor | H20 | H60 | H120 |
| --- | ---: | ---: | ---: |
| 52W High | **0.068** | **0.106** | **0.230** |
| Low Vol 63D | **0.081** | **0.147** | **0.172** |
| 6-1 Momentum | 0.047 | 0.047 | **0.100** |
| Operating Margin Acceleration | **0.060** | **0.066** | **0.090** |
| Gross Margin Acceleration | 0.044 | 0.052 | **0.085** |
| Asset Growth | 0.001 | 0.042 | 0.094 |

Values are mean test-fold IC.

## Strongest result: 52-week-high proximity

Sector-neutral:

- H20: 7 folds, mean test IC **0.068**, 86% positive folds
- H60: 4 folds, mean test IC **0.106**, 75% positive folds
- H120: 3 folds, mean test IC **0.230**, 100% positive folds
- H120 worst fold is still **+0.125**

This is currently the strongest cross-horizon stability evidence in Zincir
Kıran.

## Low volatility

Low Vol is also robust:

- H60 mean test IC: **0.147**
- H120: **0.172**
- every H60/H120 fold is positive

But there is visible late-fold degradation:

- H60 late-minus-early fold IC: about **-0.325**
- H120: about **-0.319**

So Low Vol is strong, but not regime-invariant.

## 6-1 momentum

6-1 momentum survives chronological OOS testing:

- H20: 0.047
- H60: 0.047
- H120: **0.100**
- all H60/H120 test folds are positive

The evidence is weaker than 52W High / Low Vol but materially positive.

## Financial factors

### Operating-margin acceleration

This is the most stable financial candidate:

- H20: **0.060**, 7/7 folds positive
- H60: **0.066**, 4/4 positive
- H120: **0.090**, 3/3 positive
- worst H20/H60/H120 fold remains positive

This is much stronger evidence than static profitability-level factors.

### Gross-margin acceleration

Also survives:

- H20: 0.044, 7/7 positive
- H60: 0.052, 3/4 positive
- H120: **0.085**, 3/3 positive

### Asset growth

Much less stable:

- H20: **0.001**, only 29% positive folds
- H60: 0.042, only 50% positive folds
- H120: 0.094, 67% positive folds with a negative worst fold

The long-horizon full-sample asset-growth result therefore should not be treated
as a uniformly stable factor.

## H252 boundary

After true horizon-maturity embargo, only **one independent H252 validation
fold** is available in the current 60-month history.

Therefore every H252 result is explicitly:

`INSUFFICIENT_FOLDS`

The values are retained as directional observations but cannot support a
stability classification.

## Current empirical hierarchy

Based on real-data, sector-neutral, embargoed walk-forward evidence through
H120:

1. **52W High Proximity**
2. **Low Volatility**
3. **Operating Margin Acceleration**
4. **6-1 Momentum / Gross Margin Acceleration**
5. **Asset Growth — horizon-sensitive / fragile**

This does not set production weights. Financial candidates still carry
`EXPERIMENTAL_VERSION_RISK`, and all return labels remain diagnostic proxies.
