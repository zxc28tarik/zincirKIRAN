# Experimental Semantic Financial Facts Bootstrap

Zincir Kıran can reuse a large real KAP-derived semantic financial corpus from
TOTAL-RASYO-HESAPLAYICI, but only under an explicit **EXPERIMENTAL_VERSION_RISK**
research profile.

## Source package

Source commit:
`c8b481e79e270f2c095e8c180671a3f483f0775e`

Primary semantic facts:
- path: `data/backtest_sources/experimental_semantic_facts_v1/semantic_reports.jsonl.gz`
- SHA256: `07863ddbd78924ad276e7d0aeba7fa6eec9733477b4ca3c02ece285bcf1d9e7a`
- reports: 4,581
- facts: 195,782

Predecessor/alias supplement:
- SHA256: `adb49330f29b370306d69545db1a48d34a5fda6d763a4d4bdfd2eadc56df06a3`
- reports: 3
- facts: 136

Entity supplement:
- SHA256: `d70e8a1056fd16b03a9ba44c8d6d3c183cb9e2f3604f45692d90817e5b52d741`
- reports: 468
- facts: 4,051

Total:
- **5,052 reports**
- **199,969 semantic facts**
- deterministic two-primary-read rebuild: PASS

## Historical-cell evidence

The source P3 materialization covered 60 months × 100 historical BIST100 members:
- total cells: 6,000
- cells with own-period visible financial facts: **5,633**
- score-input-ready: **0**
- explicit rejections: **6,000**

This means the corpus has substantial real financial information while the old
Total Rasyo scoring requirements still failed closed. Zincir Kıran must not
reinterpret the 6,000 Total Rasyo rejections as absence of useful raw financial
facts.

The independent source audit also verified:
- 22 original KAP archives
- 2,115 selected reports
- 118,434 financial-fact usages

## Why it remains experimental

Two source risks remain unresolved:

1. `ORIGINAL_CATALOG_BYTES_UNAVAILABLE`
2. `SUPERSEDED_HISTORICAL_KAP_REPORT_VERSIONS_NOT_ENUMERATED`

Therefore:
- authoritative PIT claim = **false**
- Production Decision evidence = **forbidden**
- Live Shadow historical backfill = **forbidden**
- champion promotion from this dataset = **forbidden**
- Factor Lab exploratory research = **allowed only with the same risk label**

## Allowed research

The corpus can accelerate exploratory tests for:
- Value
- Profitability
- Quality
- Investment
- Fundamental Acceleration
- sector-specific accounting mappings

Any result produced from this corpus must remain separately labeled from the
authoritative tournament.

## Explicitly excluded source products

Zincir Kıran does not import:
- Total Rasyo P4 scores
- Total Rasyo rankings
- Total Rasyo decisions

The only imported objects are source-bound semantic financial facts and their
lineage/risk metadata.
