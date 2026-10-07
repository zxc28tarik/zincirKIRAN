# Real Fixed-Ridge ML Challenger — Result

Implementation 40 ran successfully on GitHub Actions run **37665294593**.

Artifact: **11502153966**  
Digest: `sha256:64e3ccd48b0f0b8f8dc1044df38631f1d4b48ee3f8d0865aa25e03ea00bcdbb6`

The model specification remained unchanged after results: deterministic ridge,
`lambda=1.0`, no tuning, same five sector-neutral factors, matured train labels
only, train-only standardization.

| Horizon | Contender | Mean test IC | Mean top-quintile excess proxy | Mean Q5-Q1 | Folds |
| --- | --- | ---: | ---: | ---: | ---: |
| H20 | HIGH_52W_PROXIMITY | 0.085 | 0.87% | 0.025 | 7 |
| H20 | EW5_COMPOSITE | 0.108 | 0.94% | 0.032 | 7 |
| H20 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0.107 | 0.24% | 0.022 | 7 |
| H20 | FIXED_RIDGE_5F | 0.106 | 0.21% | 0.020 | 7 |
| H60 | HIGH_52W_PROXIMITY | 0.114 | 0.95% | 0.060 | 4 |
| H60 | EW5_COMPOSITE | 0.125 | -0.22% | 0.060 | 4 |
| H60 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0.123 | -0.78% | 0.053 | 4 |
| H60 | FIXED_RIDGE_5F | 0.113 | -1.45% | 0.034 | 4 |
| H120 | HIGH_52W_PROXIMITY | 0.223 | 3.11% | 0.182 | 3 |
| H120 | EW5_COMPOSITE | 0.201 | -0.80% | 0.130 | 3 |
| H120 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0.223 | 1.31% | 0.142 | 3 |
| H120 | FIXED_RIDGE_5F | 0.176 | 0.31% | 0.124 | 3 |
| H252 | HIGH_52W_PROXIMITY | 0.205 | 5.75% | -0.152 | 1 |
| H252 | EW5_COMPOSITE | 0.178 | 6.20% | 0.115 | 1 |
| H252 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0.223 | 2.50% | -0.124 | 1 |
| H252 | FIXED_RIDGE_5F | 0.218 | 6.59% | -0.079 | 1 |

## H20

Ridge has strong rank evidence:

- ridge IC: **0.106**
- EW5 IC: **0.108**
- 52W High IC: **0.085**

But its average top-quintile forward excess proxy is only
**0.21%**,
well below EW5 (**0.94%**)
and 52W High (**0.87%**).

So improved ranking does not translate into a superior investable long leg.

## H60

Ridge does not improve the existing hierarchy:

- ridge IC: **0.113**
- ridge long leg: **-1.45%**
- 52W High long leg: **0.95%**

Ridge loses the long-leg comparison to 52W High in **4/4 folds**.

## H120

Ridge remains statistically respectable but is not the strongest model:

- ridge IC: **0.176**
- dynamic IC: **0.223**
- 52W High IC: **0.223**

Ridge long leg is only **0.31%**,
versus **3.11%**
for 52W High.

## Learned coefficients

The fold-by-fold model is not simply equal weighting. It repeatedly learns a
large positive coefficient for 52W High Proximity. Momentum and operating-margin
acceleration become more relevant at H120, but they do not produce a composite
that beats the simple 52W benchmark.

This is an important negative result: **a trained linear ML combination does not
automatically dominate the simpler signal.**

## H252

Ridge looks strong in the single available fold, including the highest long leg
of the four contenders, but only **one independent embargoed fold** exists.
No stability conclusion is allowed.

## Decision

Do **not** promote the ridge challenger.

Implementation 40 supports keeping ML as a challenger rather than assuming
complexity is an improvement. The next portfolio-aware test should charge the
ridge model for its own turnover and historical capacity before any further
model escalation.

Financial features remain `EXPERIMENTAL_VERSION_RISK`; return labels remain
diagnostic proxies.
