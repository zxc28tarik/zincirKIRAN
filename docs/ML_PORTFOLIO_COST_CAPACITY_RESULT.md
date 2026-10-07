# ML Portfolio Cost + Capacity Tournament — Result

Implementation 41 ran successfully on GitHub Actions run **37666165189**.

Artifact: **11502159919**  
Digest: `sha256:376340e541b3f9efd806e89f64074707b0d8a47b1cd4bde2e770d68a7ff8e87b`

No portfolio or ML parameter was changed after results.

| Horizon | Contender | Gross long-leg | Turnover | Net @ 25 bps | Median capacity @ 1%/1d | Folds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| H20 | HIGH_52W_PROXIMITY | 0.93% | 0.863x | 0.72% | 25.9m TL | 7 |
| H20 | EW5_COMPOSITE | 0.91% | 0.616x | 0.75% | 25.1m TL | 7 |
| H20 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0.24% | 0.689x | 0.06% | 25.0m TL | 7 |
| H20 | FIXED_RIDGE_5F | 0.27% | 0.724x | 0.09% | 24.0m TL | 7 |
| H60 | HIGH_52W_PROXIMITY | 0.87% | 0.833x | 0.66% | 28.0m TL | 4 |
| H60 | EW5_COMPOSITE | -0.29% | 0.647x | -0.46% | 26.5m TL | 4 |
| H60 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | -0.71% | 0.767x | -0.91% | 27.2m TL | 4 |
| H60 | FIXED_RIDGE_5F | -1.32% | 0.815x | -1.53% | 27.8m TL | 4 |
| H120 | HIGH_52W_PROXIMITY | 3.19% | 0.839x | 2.98% | 26.1m TL | 3 |
| H120 | EW5_COMPOSITE | -0.78% | 0.631x | -0.94% | 25.0m TL | 3 |
| H120 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 1.25% | 0.695x | 1.08% | 22.8m TL | 3 |
| H120 | FIXED_RIDGE_5F | 0.40% | 0.760x | 0.21% | 24.6m TL | 3 |
| H252 | HIGH_52W_PROXIMITY | 5.88% | 0.718x | 5.70% | 21.8m TL | 1 |
| H252 | EW5_COMPOSITE | 6.13% | 0.614x | 5.98% | 20.4m TL | 1 |
| H252 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 2.08% | 0.632x | 1.93% | 20.6m TL | 1 |
| H252 | FIXED_RIDGE_5F | 8.18% | 0.550x | 8.05% | 14.4m TL | 1 |

## H20

Fixed ridge:

- gross long-leg: **0.27%**
- net @ 25 bps: **0.09%**
- turnover: **0.724x**
- strict 1%/1-day median capacity: **24.0m TL**

Ridge slightly improves on the train-only dynamic composite after costs, but it
remains far behind both EW5 and 52W High. Its capacity is not materially better
than the simpler models.

## H60

This is a clear failure for the current ridge challenger:

- ridge net @ 25 bps: **-1.53%**
- 52W High net @ 25 bps: **0.66%**

Ridge is the weakest long-only contender on average. Historical ADV coverage is
still 100%, so the weakness is not an execution-data artifact.

## H120

Ridge is better than equal-weight EW5 but still not competitive with the main
positive challengers:

- ridge net @ 25 bps: **0.21%**
- dynamic net @ 25 bps: **1.08%**
- 52W High net @ 25 bps: **2.98%**

The simple 52W signal remains the strongest average long leg.

## Capacity

Ridge has **zero missing ADV dates** across all tested horizons and 100% selected
ADV coverage. Its strict 1%/1-day median capacity is in the same broad range as
the other contenders.

Therefore the weak H20-H120 result cannot be dismissed as a liquidity problem.

## H252

Ridge is striking in the only available H252 fold:

- gross: **8.18%**
- net @ 25 bps: **8.05%**

But there is only one independent embargoed fold. This remains directional
evidence only and cannot support a stability or promotion decision.

## Decision

Do **not** promote FIXED_RIDGE_5F.

The current evidence says:

1. ML can produce respectable rank IC;
2. that does not automatically improve the investable long leg;
3. costs and liquidity do not rescue the current ridge model;
4. simple 52W High remains extremely difficult to beat;
5. any nonlinear ML challenger must be a new preregistered hypothesis rather
   than a post-hoc attempt to rescue this model.

This is a useful scientific result: Zincir Kıran has now rejected its first real
ML challenger under the same portfolio realism applied to the interpretable
models.
