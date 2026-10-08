# Prospective 52W Input Sufficiency + Corporate-Action Risk Gate — Result

Implementation 45D ran successfully on GitHub Actions run **37805821958**.

Artifact: **11562164197**  
Digest:
`sha256:5dd8e9c371d876e05ac18ca079fb3f1826aa1f1a70052a033d3dddba5362554a`

Frozen package commit:

`d00efdc71fbefbb7644cbebcc8627a8c7bd9ad9b`

## Price-history sufficiency

The exact current 100-name BIST100 universe was captured from July 2025 through
the prospective capture date using raw Close, Adj Close and Volume.

- requested tickers: **100**
- captured tickers: **100**
- captured daily rows: **32,880**
- vendor rejections: **0**
- tickers with at least 252 finite positive Adj Close observations: **99**

The only price-history failure is:

- **PAHOL — 224 usable Adj Close observations**

PAHOL is therefore mechanically `PRICE_HISTORY_INSUFFICIENT`.

## Official KAP gap coverage

The previously frozen complete KAP inventory ended on 2026-07-31.

45D captured the official market-wide KAP disclosure stream from
**2026-08-01 through 2026-10-08** using the proven adaptive `byCriteria`
endpoint.

Result:

- coverage: **complete**
- adaptive windows: **16**
- all disclosure rows: **18,793**
- disclosureType=CA rows: **3,634**
- current-BIST100 classified risk rows: **43**
- current-BIST100 tickers with recent CA risk: **18**

No response-cap gap or unsplittable day was accepted.

## Recent unresolved CA-risk tickers

- AKFYE: 2
- ASTOR: 1
- CVKMD: 5
- CWENE: 2
- ECILC: 1
- FENER: 1
- GUBRF: 4
- HALKB: 3
- HEKTS: 2
- KATMR: 1
- KORDS: 4
- MAVI: 2
- RGYAS: 6
- RYSAS: 2
- SASA: 3
- SOKM: 1
- TKFEN: 2
- TRGYO: 1

These events include bonus/rights/capital-change processes, dividend processes
and mergers. The classifier is a **risk screen**, not proof of economic
resolution. No ex-date, ratio, cash amount or payment date is invented.

Therefore all 18 names remain `RECENT_CA_RISK_UNRESOLVED`.

## Remaining 81 names

The remaining 81 names satisfy:

- current universe membership;
- sufficient captured 252-day price history;
- complete Aug→current KAP gap;
- no classified unresolved recent CA-risk disclosure.

They are **still not allowed to score**.

Reason:

`HISTORICAL_CA_RECONCILIATION_REQUIRED`

The older portion of the actual 252-observation lookback overlaps the frozen
historical KAP inventory. That historical positive-event evidence must be
reconciled ticker-by-ticker before the raw/adjusted price path is accepted for a
prospective 52W factor.

## Gate result

- price history insufficient: **1**
- unresolved recent CA risk: **18**
- historical CA reconciliation required: **81**
- score computation allowed: **0**
- shadow signal allowed: **0**

This confirms the input-sufficiency gate works as intended. 45B's coarse domain
presence cannot accidentally unlock the 52W track.

## Decision

Do not emit a 52W score yet.

The next narrow task is historical corporate-action reconciliation for the
actual 252-day lookback, followed by detailed handling or exclusion of the 18
recent-risk names.

Implementation 45D creates no real shadow run, order, production threshold or
champion promotion.
