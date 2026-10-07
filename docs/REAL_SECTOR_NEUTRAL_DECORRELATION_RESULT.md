# Real Sector-Neutral / De-correlation Result

The combined real-data diagnostic covered **13 factors**:

- 5 price factors
- 8 currently materializable financial factors

All **5,988 price rows** and all **5,087 financial-factor rows** had a valid
historical broad-sector route.

## Main profitability question

Sector composition explains different amounts of the raw negative
profitability signal.

| Factor | H252 raw IC | H252 sector-neutral IC | Result |
| --- | ---: | ---: | --- |
| Gross profitability | -0.059 | **+0.020** | sign flips; sector mix was dominant |
| Operating profitability | -0.108 | **-0.066** | negative signal materially weakens but survives |
| ROA | -0.146 | **-0.118** | still strongly negative; sector mix is not enough |
| Operating margin | -0.076 | **-0.092** | sector-neutral result is worse |

Therefore the earlier negative ROA result cannot be dismissed as a simple
sector-composition artifact.

The gross-profitability result is different: once broad-sector composition is
removed, its negative raw IC disappears and becomes mildly positive.

## Acceleration / investment discipline

Operating-margin acceleration improves after sector neutralization:

- H120: 0.044 → **0.049**
- H252: 0.040 → **0.055**
- H252 ICIR: 0.283 → **0.416**

Gross-margin acceleration remains positive and is essentially unchanged at
H120:

- 0.049 raw → **0.049 sector-neutral**

Asset growth remains useful at H252:

- raw IC: 0.099
- sector-neutral IC: **0.088**
- sector-neutral ICIR: **0.578**

This indicates that the long-horizon investment-discipline signal is not only
a sector allocation effect.

## Price factors remain robust

52-week-high proximity remains the strongest tested signal after broad-sector
neutralization:

- H120 IC: 0.212 → **0.178**
- H252 IC: 0.198 → **0.161**
- H252 ICIR: **1.244**

Low volatility also survives:

- H252 IC: 0.183 → **0.169**
- H252 ICIR actually improves from 1.278 to **1.343**

6-1 and 12-1 momentum remain positive, but part of their raw signal was sector
exposure.

## De-correlation result

At the preregistered **|mean Spearman rho| >= 0.70** threshold, there are:

**0 redundancy candidates.**

Highest sector-neutral pairwise correlations:

1. gross-margin acceleration vs operating-margin acceleration: **0.669**
2. gross margin vs operating margin: **0.662**
3. operating profitability vs ROA: **0.634**
4. 12-1 momentum vs 6-1 momentum: **0.632**

These pairs are economically related and close enough to deserve continued
monitoring, but the locked threshold does not permit us to call them redundant.

## Boundary

This remains diagnostic evidence. In particular:

- financial data retains EXPERIMENTAL_VERSION_RISK;
- sector groups are broad XUSIN/XUHIZ/XUMAL/XUTEK routes, not fine industries;
- future returns remain the adjusted-close-minus-XU100 proxy;
- no factor is deleted, residualized, promoted or reweighted by this result.
