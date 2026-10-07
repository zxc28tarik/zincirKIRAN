# Extended H252 Portfolio Realism — Result

Implementation 43 ran successfully on GitHub Actions run **37689106767**.

Artifact: **11512019476**  
Digest: `sha256:6d592f7446dc12997e90bc4e200a6c0c5c3bca903bbf67bdfe91bc7ed256adc7`

## Sanity gate

Before opening the extended result, the original one-fold H252 portfolio path
was rerun.

Implementation 41's gross return, turnover, 10/25/50 bps net-return, ADV
coverage and capacity aggregates reproduced within the preregistered tolerance.

**SANITY PASS = TRUE**

## Extended two-fold result

| Contender | Mean gross long-leg | Mean turnover | Mean net @ 25 bps | Median capacity @ 1%/1d | Positive net folds |
| --- | ---: | ---: | ---: | ---: | ---: |
| HIGH_52W_PROXIMITY | 14.28% | 0.927x | 14.04% | 22.0m TL | 0.50 |
| EW5_COMPOSITE | -6.04% | 0.668x | -6.21% | 26.6m TL | 0.00 |
| TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | -2.89% | 0.730x | -3.07% | 25.2m TL | 0.00 |
| FIXED_RIDGE_5F | -1.72% | 0.837x | -1.92% | 19.9m TL | 0.50 |

The dominant result is the 52-week-high signal:

- mean gross forward-excess proxy: **14.28%**
- mean net @ 25 bps: **14.04%**
- ridge mean net @ 25 bps: **-1.92%**
- ridge minus 52W @ 25 bps: **-15.97%**
- ridge beats 52W after costs in **0/2 folds**.

## Fold detail

- **H252-F2** (2023-09-01 → 2024-02-01): HIGH_52W_PROXIMITY: -7.41%; EW5_COMPOSITE: -6.52%; TRAIN_ONLY_EVIDENCE_WEIGHTED_5F: -3.47%; FIXED_RIDGE_5F: -9.01%
- **H252-F3** (2025-03-03 → 2025-06-02): HIGH_52W_PROXIMITY: 35.50%; EW5_COMPOSITE: -5.90%; TRAIN_ONLY_EVIDENCE_WEIGHTED_5F: -2.67%; FIXED_RIDGE_5F: 5.16%

This is the main caution on 52W High: its two-fold average is excellent, but
the long-only sign is not stable. The first independent fold is negative; the
second is strongly positive. Rank-IC stability from Implementation 42D and
long-leg stability are therefore still different concepts.

## Liquidity / capacity

Every contender has:

- zero missing ADV validation dates;
- 100% selected-name ADV coverage.

Under the strict 1% participation / 1-day scenario, mean fold median capacity is:

- 52W High: **22.0m TL**
- EW5: **26.6m TL**
- Dynamic: **25.2m TL**
- Ridge: **19.9m TL**

Thus the ridge failure is not explained by absent liquidity evidence.

## Decision

Do **not** promote ridge.

Do **not** automatically promote a new production champion or choose a
production cost/liquidity threshold from this result.

Implementation 43 strengthens the investment-relevant H252 conclusion from
42D: the former single-fold ridge advantage disappears when a second genuinely
independent fold is added and portfolio realism is applied.

52W High is currently the strongest average H252 long-only contender in this
two-fold sample, but its fold-level long-leg sign instability means additional
independent history remains valuable.
