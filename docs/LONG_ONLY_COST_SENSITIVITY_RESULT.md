# Long-Only Turnover / Cost-Sensitivity — Result

Implementation 38 ran successfully on GitHub Actions run **37662161280**.

Artifact: **11501626922**  
Digest: `sha256:b8bcd7c3633d776817bf415dd05612e95ea2f3c6e220756d24d4c22bce40797b`

The preregistered setup was not changed after seeing results:

- exact 5-of-5 common panel;
- top 20% long-only, equal-weight;
- fold boundary reset to cash;
- Implementation 35 purge / embargo;
- Implementation 37 train-only dynamic weights;
- 10 / 25 / 50 bps cost-sensitivity grid.

The bps values are **scenarios**, not claimed historical spread/slippage observations.

## Headline results

| Horizon | Contender | Mean gross forward excess proxy | Mean gross turnover | Mean net @ 25 bps | Folds |
| --- | --- | ---: | ---: | ---: | ---: |
| H20 | HIGH_52W_PROXIMITY | 0.93% | 0.863x | 0.72% | 7 |
| H20 | EW5_COMPOSITE | 0.91% | 0.616x | 0.75% | 7 |
| H20 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0.24% | 0.689x | 0.06% | 7 |
| H60 | HIGH_52W_PROXIMITY | 0.87% | 0.833x | 0.66% | 4 |
| H60 | EW5_COMPOSITE | -0.29% | 0.647x | -0.46% | 4 |
| H60 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | -0.71% | 0.767x | -0.91% | 4 |
| H120 | HIGH_52W_PROXIMITY | 3.19% | 0.839x | 2.98% | 3 |
| H120 | EW5_COMPOSITE | -0.78% | 0.631x | -0.94% | 3 |
| H120 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 1.25% | 0.695x | 1.08% | 3 |
| H252 | HIGH_52W_PROXIMITY | 5.88% | 0.718x | 5.70% | 1 |
| H252 | EW5_COMPOSITE | 6.13% | 0.614x | 5.98% | 1 |
| H252 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 2.08% | 0.632x | 1.93% | 1 |

## H20

52W High and EW5 are nearly tied before costs:

- 52W High gross: **0.93%**
- EW5 gross: **0.91%**

But EW5 turnover is much lower:

- 52W High: **0.863x**
- EW5: **0.616x**

At 25 bps, EW5 moves slightly ahead:

- EW5: **0.75%**
- 52W High: **0.72%**

At 50 bps the difference widens in EW5's favor. The dynamic challenger is
materially weaker on the H20 long leg and becomes negative on mean at 50 bps.

## H60

52W High remains the clear benchmark:

- gross: **0.87%**
- net @ 25 bps: **0.66%**

EW5 and train-only dynamic have negative mean gross forward-excess proxies, and
costs make them worse. No composite promotion is supported at H60.

## H120

This horizon produces the most important comparison with Implementation 37.

Train-only dynamic again beats EW5 in **3/3** paired folds. Mean gross
difference versus EW5 is **2.03%**,
and the advantage remains about **2.02%**
at 25 bps.

However, 52W High has the stronger average long leg:

- 52W High gross: **3.19%**
- dynamic gross: **1.25%**
- 52W High net @ 25 bps: **2.98%**
- dynamic net @ 25 bps: **1.08%**

Dynamic beats 52W High in 2/3 paired folds but loses on the mean because one
fold favors 52W High strongly.

This is a useful distinction: the dynamic model's H120 rank IC can match 52W
High while its top-quintile long leg is still weaker on average.

## H252

Only one independent embargoed fold exists. EW5 is highest in that single
fold, but **no stability conclusion is allowed**.

## Decision

Do **not** replace the general benchmark champion.

The new evidence changes the interpretation in a useful way:

- **H20:** EW5 is the more cost-efficient challenger and can edge 52W High under
  moderate/high cost scenarios because its turnover is lower.
- **H60:** retain 52W High clearly.
- **H120:** retain train-only dynamic as a strong composite challenger to EW5,
  but 52W High still has the stronger average long leg.
- **H252:** insufficient folds.

Most importantly, **IC evidence and long-only portfolio evidence are not the
same thing**. Implementation 38 confirms why Long-Leg Validation was added to
the research constitution.

This remains `EXPERIMENTAL_VERSION_RISK`; it is not a self-financing NAV
backtest, does not claim observed execution costs, does not establish capacity,
and cannot promote a production model.
