# Pre-2021 Coverage / H252 Power Audit — Result

Implementation 42B completed as a **coverage-only** diagnostic. No IC, factor
return, long-leg return, model fit, or portfolio result was calculated.

GitHub Actions run: **37675228514**  
Artifact: **11506927721**  
Digest: `sha256:2d1f445c02a4c65ea07ad718f005bf489697a1a0e066acc3edc40dc83bf5e015`

## Sanity result

The final audit reproduces the existing research boundary correctly:

- current frozen signal dates: **60**
- current H252-evaluable dates: **47**
- current evaluated H252 folds: **1**
- expected from Implementation 35: **1**
- sanity: **PASS**

Two protocol amendments were recorded before any H252 performance rerun:

1. the existing period uses the frozen M3 XU100 calendar rather than a refreshed
   Yahoo calendar;
2. a fold counts only if at least three validation months have at least 20
   usable common factor/target rows.

These changes correct data-authority and fold-count semantics; they do not use
alpha results.

## Historical market recoverability

The reconstructed 2019-04..2021-07 universe contains:

- **28** monthly signals;
- **2800** membership cells;
- **152** distinct historical ticker codes;
- exactly **100 members in every month**.

Direct historical-code Yahoo discovery:

- requested: **152**
- non-empty history: **141**
- empty/failed: **11**

Failed direct codes:

`ADANA, ANACM, DGKLB, GUSGR, IPEKE, ITTFH, KERVT, KOZAA, KOZAL, SODA, TRKCM`

No successor alias was used to make a row eligible. For example, GUSGR is
reported as a lineage candidate to TURSG, and TURSG has pre-effective Yahoo
history, but that history is not silently substituted into this audit.

## What actually limits the early history

The main bottleneck is **not raw price history**.

| Signal date | Exact price | 52W | Sector route | Gross-margin accel. | Operating-margin accel. | Five-factor rows | H252-test rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2019-04-01 | 91 | 90 | 0 | 0 | 0 | 0 | 0 |
| 2020-07-01 | 92 | 92 | 0 | 0 | 0 | 0 | 0 |
| 2020-08-04 | 92 | 92 | 88 | 13 | 13 | 12 | 12 |
| 2020-09-01 | 92 | 92 | 88 | 74 | 74 | 67 | 67 |
| 2021-01-04 | 96 | 96 | 92 | 78 | 78 | 70 | 70 |
| 2021-07-01 | 96 | 94 | 100 | 83 | 83 | 75 | 75 |

In 2019, roughly 90–91 names already have direct price/52W/H252 endpoint
coverage, but the existing sector-route and financial-acceleration evidence has
zero usable coverage.

The transition is sharp:

- **2020-08-04:** only 12 five-factor rows, below the 20-name test minimum.
- **2020-09-01:** 67 five-factor/H252-test rows — the first mechanically usable
  extension month.
- **2021-07-01:** 75 five-factor/H252-test rows.

So acquiring substantially earlier prices alone would not unlock the current
five-factor engine before September 2020. Earlier research would first require
new audited sector/fundamental evidence.

## H252 power gain before performance is opened

Mechanically eligible pre-anchor signal dates:

- 2020-09-01
- 2020-10-01
- 2020-11-02
- 2020-12-01
- 2021-01-04
- 2021-02-01
- 2021-03-01
- 2021-04-01
- 2021-05-03
- 2021-06-01
- 2021-07-01

That is **11**
additional usable months.

Using the same maturity purge, validation embargo, minimum 18 train months and
minimum 3 evaluable validation months:

- current expected evaluated H252 folds: **1**
- extended expected evaluated H252 folds: **2**
- net gain: **+1 fold**

The extension therefore has real statistical value: it can move H252 from one
independent evaluated fold to **two**.

It does **not** yet justify running the performance test, because the Yahoo
discovery rows are live vendor evidence, not a frozen historical market
artifact.

## Next acquisition boundary

The efficient next step is narrow:

1. freeze/hash market history needed for the mechanically eligible
   **2020-09..2021-07** extension;
2. reconcile direct failures and approved ticker lineage without guessing;
3. create an extended immutable common-panel input;
4. recompute the fold-count receipt again;
5. only then open H252 factor/model results.

Parent issue #104 remains open until that frozen extension exists.
