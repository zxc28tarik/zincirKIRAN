# Extended H252 Champion–Challenger Tournament

Implementation 42D is the first performance-opening step after the historical
data extension.

It is deliberately **H252-only**.

## Frozen inputs

The original 60-month common panel remains untouched.

The only appended evidence is the frozen 42C package for September 2020 through
July 2021:

- price SHA256:
  `e0894027610988651d9ffec6cb53cad5bcfc41ae7dbd132d5e55af06c7afcf5e`
- membership SHA256:
  `ce691744788fb74f8c904b2aa8b34528140d0785e6507989096362bb226c93ab`

Financial acceleration factors reuse the exact existing frozen semantic corpus.
Sector-neutralization reuses the exact existing historical sector routes.
The XU100 calendar/benchmark is the existing frozen source.

## Sanity gate before extension performance

Before a single extended result is accepted, the runner rebuilds the existing
60-month common panel and reruns the fixed-ridge H252 tournament.

It must reproduce:

- exactly one evaluated H252 fold;
- the previously persisted H252 IC, top-quintile and Q5-Q1 aggregates for all
  four contenders within 1e-12.

If that fails, the extended performance run aborts.

## Appended panel construction

For the eleven frozen early signal months:

1. price factors and TARGET_252 use the existing price-factor formulas;
2. financial accelerations use the existing PIT semantic materializer;
3. all five factors are sector-neutralized with the same broad-sector rule;
4. all five scores are required;
5. EW5 remains fixed at 20% per factor.

No missing value is neutral-filled.

## Tournament

Contenders remain unchanged:

- HIGH_52W_PROXIMITY
- EW5_COMPOSITE
- TRAIN_ONLY_EVIDENCE_WEIGHTED_5F
- FIXED_RIDGE_5F

Walk-forward rules remain unchanged:

- 18 initial signal months;
- six-month validation blocks;
- minimum three valid validation months;
- matured training labels only;
- horizon-maturity validation embargo;
- dynamic weights use train IC only;
- fixed ridge lambda = 1.0;
- no tuning.

The primary question is whether the additional independent H252 evidence
confirms or rejects the earlier single-fold ridge advantage.

No automatic champion or production promotion is authorized.
