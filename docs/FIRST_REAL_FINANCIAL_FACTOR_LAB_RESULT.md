# First Real Financial Factor Lab — Result

The first real financial-factor diagnostic ran successfully against the locked
experimental semantic corpus.

## Coverage

- 5,052 semantic reports
- 199,969 semantic facts
- 6,000 historical BIST100 membership cells
- 5,633 cells had some visible semantic financial evidence
- 5,087 cells materialized at least one financial factor
- all 60 signal dates represented

Eight factors produced usable observations. Accruals, CFO/assets and
CapEx/assets did not yet produce a valid explicit-quarter TTM series and remain
unavailable rather than being neutral-filled.

## Direction-normalized mean IC

| Factor | H20 | H60 | H120 | H252 |
| --- | ---: | ---: | ---: | ---: |
| Asset growth (lower better) | -0.008 | -0.007 | 0.003 | **0.099** |
| Gross margin | 0.012 | -0.006 | -0.013 | -0.053 |
| Gross margin acceleration | **0.037** | **0.044** | **0.049** | 0.005 |
| Gross profitability | -0.007 | -0.023 | -0.025 | -0.059 |
| Operating margin | 0.008 | -0.014 | -0.031 | -0.076 |
| Operating margin acceleration | **0.028** | **0.031** | **0.044** | **0.040** |
| Operating profitability | -0.009 | -0.031 | -0.056 | -0.108 |
| ROA | -0.006 | -0.036 | -0.061 | **-0.146** |

## Initial interpretation

The most interesting positive signals are:

1. **Asset growth / investment discipline at H252** — mean IC 0.099, ICIR 0.659
   after direction normalization, meaning lower asset growth ranks better.
2. **Gross-margin acceleration at H20/H60/H120** — mean IC 0.037/0.044/0.049.
3. **Operating-margin acceleration** — positive at every horizon,
   0.028/0.031/0.044/0.040.

Static profitability levels are negative at medium/long horizons in this raw
diagnostic, especially ROA and operating profitability. This is not yet a
basis for reversing their economic priors.

Before interpreting those negative signs as genuine BIST effects, the next
tests must isolate:
- sector composition / sector-neutral ranks,
- TMS 29 and accounting-regime effects,
- historical version risk,
- outliers/winsorization,
- factor redundancy,
- overlapping H252 labels.

Authority remains `EXPERIMENTAL_VERSION_RISK`. No production, champion or
LAB_VALIDATED promotion follows from this run.
