# First Experimental Factor Lab Run

This implementation turns dated candidate-factor observations into repeatable
experimental Factor-Lab evidence.

## Per-date evaluation

For every signal date:
- usable / total observation count
- coverage
- Spearman rank IC
- quantile mean future market-relative returns
- quantile monotonicity
- top-quantile excess return
- bottom-quantile excess return
- top-minus-bottom spread

Missing factor/label rows are excluded with visible coverage loss. They are
never converted to zero or a neutral rank.

## Direction normalization

The raw factor value is preserved.

For research evaluation only:
- HIGHER_IS_BETTER: factor value unchanged
- LOWER_IS_BETTER: sign is reversed before ranking / IC

This allows all reported ICs and quantile orderings to share the interpretation
"higher standardized factor score is expected to be better" without mutating
stored raw observations.

## Across-date evaluation

The run reports:
- valid / total IC periods
- mean IC
- ICIR
- mean coverage
- mean top-vs-market return
- mean top-minus-bottom spread

A date with too few usable observations remains an explicit unavailable period.

## Liquidity robustness

Liquidity tiers are never guessed.

If observations explicitly contain tiers such as:
- LIQUID_50
- LIQUID_25

the exact same cross-sectional evaluation is repeated separately for each tier.

This is the operational implementation of the Research Constitution's
Liquidity-Tier Robustness requirement.

## Authority

Every result from this runner is:
`EXPERIMENTAL_VERSION_RISK`

It cannot directly authorize:
- LAB_VALIDATED
- champion promotion
- Live Shadow production-equivalent claims
- Production Gate evidence

It exists to discover which candidate definitions deserve authoritative
re-testing after financial version coverage is fixed.

## First full research matrix

With 16 current factor definitions and four horizons, the intended initial
matrix is **64 factor × horizon experiments**, before alternative definitions.

Every experiment must have a preregistered:
- dataset id
- factor id/version
- horizon
- quantile count
- cost model id
- expected direction
- timestamp
