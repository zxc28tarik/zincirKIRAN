# Extended H252 Champion–Challenger Tournament — Result

Implementation 42D ran successfully on GitHub Actions run **37687970807**.

Artifact: **11511468267**  
Digest: `sha256:3f41efe1a931523919a8b5555df33e35f9868b028fd3a61e7e4dc30bf5d792ab`

## Sanity gate

Before opening extended H252 performance, the runner reran the original frozen
60-month common panel.

- expected H252 evaluated folds: **1**
- observed: **1**
- previously persisted IC / top-quintile / Q5-Q1 aggregates for all four
  contenders reproduced within **1e-12**

**SANITY PASS = TRUE**

The historical extension therefore did not silently alter the old result.

## Panel extension

- original common panel: **4,647 rows / 60 dates**
- frozen early extension: **813 rows / 11 dates**
- extended panel: **5,460 rows / 71 dates**
- evaluated H252 folds: **2**

The early eleven months each contain 70–79 exact five-factor H252 rows.

## Two-fold H252 result

| Contender | Mean test IC | Worst fold IC | Positive folds | Mean top-quintile excess proxy | Mean Q5-Q1 | Stability |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 52W High | 0.163 | 0.162 | 100.00% | 13.82% | 0.375 | STRONG_STABILITY |
| EW5 | 0.200 | 0.160 | 100.00% | -5.69% | 0.195 | STRONG_STABILITY |
| Train-only Dynamic | 0.214 | 0.135 | 100.00% | -2.94% | 0.186 | STRONG_STABILITY |
| Fixed Ridge | 0.126 | 0.112 | 100.00% | -1.82% | 0.188 | STRONG_STABILITY |

## The ridge result is reversed

Before the historical extension, ridge looked unusually attractive in the only
available H252 fold.

With two independent evaluable folds:

- ridge mean IC: **0.126**
- 52W High mean IC: **0.163**
- ridge mean long leg: **-1.82%**
- 52W High mean long leg: **13.82%**

Ridge beats 52W High in:

- IC folds: **0 / 2**
- long-leg folds: **0 / 2**

The previous one-fold ridge advantage is therefore **not confirmed**. The added
independent evidence rejects it.

## Fold detail

### Fold H252-F2 — validation 2023-09 to 2024-02

- 52W High IC: **0.165**
- Dynamic IC: **0.294**
- Ridge IC: **0.112**
- 52W High long leg: **-7.64%**
- Ridge long leg: **-8.90%**

### Fold H252-F3 — validation 2025-03 to 2025-06

- 52W High IC: **0.162**
- Dynamic IC: **0.135**
- Ridge IC: **0.139**
- 52W High long leg: **35.29%**
- Ridge long leg: **5.25%**

52W High has positive rank IC in both folds, but its long leg changes from
negative in the first fold to very strong positive in the second. This again
shows why rank stability and long-leg stability must be tracked separately.

## Dynamic weights

Both H252 folds put almost all dynamic weight on:

- 52W High
- Low Volatility

Momentum receives a small weight. Operating-margin acceleration and
gross-margin acceleration receive **0 weight in both folds** because matured
train evidence does not justify positive H252 weight under the locked rule.

## Decision

Do **not** promote ridge.

Do **not** replace the general champion automatically.

Implementation 42D materially upgrades H252 evidence from one to two evaluated
folds and allows a real H252 IC-stability classification. The strongest
investment-relevant conclusion is negative: the prior single-fold ML advantage
was a fragile observation.

Parent issue #104's minimum objective—more than one genuinely evaluable H252
fold using auditable historical data—has now been achieved. Two folds are still
a small sample, so further independent history would remain valuable.
