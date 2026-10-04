# Cross-Project Evidence Reuse

Zincir Kıran may reuse evidence from `TOTAL-RASYO-HESAPLAYICI`, but reuse is authority-scoped.

## Immediately reusable

### Historical benchmark / sector index closes

Source: Total Rasyo PR #15, head `445e9a7cb788124a52fd4ac171f3e16e6c67137e`.

- `index_closes.csv.gz`
- 7,415 rows
- XU100, XUSIN, XUHIZ, XUMAL, XUTEK
- 2020-07-27 through 2026-07-01
- SHA256: `32a740f7a7114e03c885d1ae75c8bacd081b5254b043521fd76ca5f8e34e786e`

Authority: **CANONICAL_PIT** for benchmark/sector index closes in the covered range.

It does **not** solve single-stock execution prices or volume.

### Historical sector routing

Same PR #15:

- 209 historical tickers
- 210 half-open route rows
- 60 signal dates / 6,000 membership cells
- SHA256: `f0c28c7babd018eb8994afdf4911a9d338dad43b291a1084a7acc47a3919c478`

Authority: **CANONICAL_PIT** for the package's historical sector routing scope.

## Reusable with restrictions

### KAP bulk financial archives

Total Rasyo PR #38 contains real official KAP bulk archives and acquisition receipts.

Evidence includes:
- 28 archives
- 994 matched insurance/finance reports
- 71 source entities
- 917 exact role/row/label identities

The raw archive evidence is reusable. However, PR #38 explicitly states that superseded-version enumeration remains unresolved, so it is **not** promoted to complete authoritative historical PIT financial coverage.

Authority:
- raw archive bytes/receipts: **RAW_EVIDENCE_ONLY**
- schema/mapping conclusions: **DISCOVERY_ONLY**

### Corporate actions

Total Rasyo PR #41 contains a large real KAP corporate-action inventory and audit receipts.

Positive event records with publication provenance may be reused. A later-collected search result alone must not be interpreted as proof that an action did not exist historically.

Authority: **POSITIVE_EVENT_ONLY** unless a contemporaneously archived source independently proves absence.

## Never imported as training labels

The following Total Rasyo outputs are not ground truth for Zincir Kıran:

- Total Rasyo scores
- M1/M2/M3/Ek scores
- AL/İZLE/UZAK decisions
- valuation scores

They may be studied as candidate features or prior-model outputs only under a separately preregistered experiment. They cannot replace forward market-relative returns.

## Practical impact

This reuse immediately removes the need to re-procure:
- benchmark/sector index close history for the PR #15 covered period;
- the corresponding historical sector-route evidence.

It materially accelerates:
- KAP financial schema discovery;
- corporate-action event ingestion.

Remaining hard blockers still include full single-stock historical prices/volume and complete authoritative PIT financial-version history.
