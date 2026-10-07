# Accounting-Regime / Subperiod Diagnostic Result

This test does **not** contain a company-level TMS 29 flag. The current semantic
corpus does not expose a reliable `inflation_adjusted` field for every
historical observation.

Therefore the two dates tested here are explicitly calendar proxies:

- 2024-01-01
- 2024-04-01

The 2024-04 split is the primary transition proxy.

## Main result: ROA is not a post-2023-only problem

Sector-neutral ROA:

| Horizon | Pre 2024-04 | Post 2024-04 | Post − Pre |
| --- | ---: | ---: | ---: |
| H60 | -0.059 | **+0.017** | +0.076 |
| H120 | -0.098 | **+0.042** | +0.140 |
| H252 | -0.183 | **+0.020** | +0.203 |

The raw score gives the same qualitative result.

So the hypothesis “ROA became negative because the 2023/2024 inflation
accounting regime entered the data” is **not supported** by this diagnostic.
The negative ROA signal is actually concentrated in the earlier sample.

H252 sector-neutral annual means make this clear:

- 2022: **-0.116**
- 2023: **-0.177**
- 2024: **-0.110**
- 2025 matured months: **+0.121**

The 2025 H252 value has only six mature signal months and should be treated as
early evidence, not a stable regime estimate.

## Operating profitability tells the same broad story

Sector-neutral H252:

- pre 2024-04: **-0.112**
- post 2024-04: **+0.032**

Annual H252:
- 2022: -0.177
- 2023: -0.016
- 2024: -0.010
- 2025 matured months: +0.069

Again, the negative full-sample IC is driven substantially by the older part
of the sample, not by a new 2024-only deterioration.

## Gross profitability is the exception

Gross profitability becomes worse after the transition proxy:

| Horizon | Pre 2024-04 | Post 2024-04 |
| --- | ---: | ---: |
| H60 | +0.036 | **-0.029** |
| H120 | +0.054 | **-0.010** |
| H252 | +0.052 | **-0.050** |

This is consistent with an accounting-regime sensitivity hypothesis, but it
does **not** prove TMS 29 causality. A company-level inflation-adjustment flag
is still required before making that attribution.

## Margins and acceleration

Operating margin improves sharply after the transition proxy:

- H120: -0.080 → **+0.034**
- H252: -0.153 → **+0.036**

Operating-margin acceleration becomes materially stronger:

- H120: +0.022 → **+0.087**
- H252: +0.031 → **+0.107**

Gross-margin acceleration also strengthens:

- H120: +0.033 → **+0.074**
- H252: +0.008 → **+0.041**

So the post-transition sample favors **change / acceleration** more strongly
than static profitability levels.

## Investment discipline

Asset growth remains interesting, but its H252 strength is concentrated in
the earlier sample:

- pre 2024-04: **+0.119**
- post 2024-04: **+0.021**

That does not invalidate the factor, but it makes regime stability a real
question for the next tournament.

## Conclusion

Current evidence says:

1. ROA's negative full-sample result is **not explained by the 2024 transition
   proxy**; the older sample is more negative.
2. Operating profitability behaves similarly.
3. Gross profitability is the factor that genuinely deteriorates after the
   proxy breakpoint.
4. Margin acceleration strengthens after the breakpoint.
5. A causal TMS 29 conclusion is forbidden until observation-level accounting
   regime metadata is acquired.

Authority remains `EXPERIMENTAL_VERSION_RISK`. No weight or production
decision follows from this test.
