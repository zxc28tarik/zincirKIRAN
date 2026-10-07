# Nested Train-Only Evidence-Weighted Composite — Result

The preregistered train-only weighting rule ran successfully.

Every fold weight was estimated only from matured training dates:

`w_i = max(train_mean_IC_i, 0) / sum_j(max(train_mean_IC_j, 0))`

No validation observation entered the weights.

## OOS results

| Horizon | Train-only dynamic | EW5 | 52W High |
| --- | ---: | ---: | ---: |
| H20 | **0.1072** | 0.1085 | 0.0849 |
| H60 | **0.1234** | 0.1246 | 0.1136 |
| H120 | **0.2227** | 0.2007 | **0.2226** |
| H252 | 0.2232 | 0.1783 | 0.2048 |

H252 still has only one independent embargoed fold and cannot support a
stability conclusion.

## H20

Dynamic weighting is effectively tied with EW5 in average IC:

- dynamic: 0.1072
- EW5: 0.1085
- difference: -0.0012

It still beats 52W High by +0.0223 mean IC and does so in 6/7 folds.

EW5 itself remains the cleaner H20 challenger because it is simpler and
slightly better on average.

## H60

Again nearly tied with EW5:

- dynamic: 0.1234
- EW5: 0.1246
- difference: -0.0012

Dynamic beats 52W High in 3/4 folds and has a less negative worst fold than
EW5 (-0.0055 versus -0.0230), but the mean advantage over EW5 is absent.

## H120

This is where train-only adaptation adds clear value:

- dynamic: **0.2227**
- 52W High: **0.2226**
- EW5: 0.2007

Dynamic beats EW5 in all **3/3** paired folds and beats 52W High in **2/3**.
Its worst fold remains strongly positive at **+0.144 IC**.

So the train-only rule fixes the main weakness of equal weighting: it does not
dilute the dominant H120 52W High signal as heavily.

## Weight behavior

Weights evolve from prior evidence rather than being manually set.

For example H20:
- first fold gives 52W High about 60.4%;
- by the last fold it falls to 34.0%;
- Low Vol rises to 29.4%;
- 6-1 Momentum holds 15.5%;
- the two margin-acceleration factors together receive about 21.1%.

At the last H120 fold:
- 52W High: 37.9%
- Low Vol: 27.4%
- 6-1 Momentum: 20.1%
- Gross Margin Acceleration: 7.1%
- Operating Margin Acceleration: 7.5%

This is genuine train-only adaptation, not validation tuning.

## Decision

Do **not** replace the general benchmark champion yet.

Current interpretation:
- H20: EW5 remains simplest/best challenger;
- H60: EW5 and train-only dynamic are effectively tied;
- H120: train-only dynamic is the strongest composite challenger and matches
  52W High while improving materially on EW5;
- H252: insufficient independent folds.

The nested dynamic composite should remain a strong challenger for the next
portfolio/cost-aware stage, but no automatic production promotion is allowed.
