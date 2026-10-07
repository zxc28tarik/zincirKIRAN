# Winsorization / Outlier Robustness Result

The first cross-sectional outlier robustness test covered **11 real factors**
across H20/H60/H120/H252.

All clipping thresholds were calculated independently inside each signal date.
No full-sample threshold was used.

## Core result

**Winsorization does not explain the profitability results.**

Across every tested factor × horizon combination:

- 1/99 winsorization produced **zero sign flips**;
- 2.5/97.5 winsorization produced **zero sign flips**;
- per-date z-scoring after 1/99 winsorization produced **zero sign flips**;
- the largest absolute change in mean IC from winsorization was only
  **0.00036**.

That is tiny relative to the signals being investigated.

The reason is also statistically intuitive: the Factor Lab evaluates Spearman
rank IC. Monotonic clipping or z-score transforms preserve almost all
cross-sectional ordering. Extreme magnitudes therefore cannot easily create a
large rank signal by themselves.

## ROA

H252:

- raw IC: **-0.146**
- winsor 1/99: **-0.146**
- winsor 2.5/97.5: **-0.145**
- sector-neutral: **-0.118**

The negative ROA result is therefore **not an artifact of a few extreme
profit/loss observations**.

Its raw Q5-Q1 spread is also large and negative at about **-28.8%** on the
diagnostic H252 return proxy. Sector neutralization reduces that magnitude but
does not reverse it.

## Operating profitability

H252:

- raw: **-0.108**
- winsor 1/99: **-0.108**
- winsor 2.5/97.5: **-0.108**
- sector-neutral: **-0.066**

Again, raw-value outliers explain essentially none of the negative IC.
Sector composition explains much more.

## Gross profitability

H252:

- raw: **-0.059**
- winsor 2.5/97.5: **-0.059**
- sector-neutral: **+0.020**

This is especially useful: the sign reversal found earlier is a **sector
composition effect**, not a winsorization/outlier effect.

## Positive factors are equally robust

H252 examples:

- Asset Growth: 0.0992 raw → **0.0992 winsorized**
- 52W High: 0.1983 raw → **0.1983 winsorized**
- Low Vol: 0.1826 raw → **0.1826 winsorized**
- Operating Margin Acceleration: 0.0402 raw → **0.0405** under the stronger
  2.5/97.5 clipping

So the strongest positive signals are not being manufactured by a few extreme
factor values either.

## Conclusion

Outlier clipping is **not** the explanation for the unusual profitability
results.

The hierarchy of likely explanations is now:

1. time/regime behavior;
2. sector composition for some factors;
3. financial-version/accounting comparability risk;
4. genuine BIST cross-sectional behavior;
5. raw-value outliers — now strongly downgraded as an explanation.

Authority remains `EXPERIMENTAL_VERSION_RISK`. No factor weight or production
decision follows from this diagnostic.
