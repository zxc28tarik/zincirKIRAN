# Free-First Data Source Matrix v0.1

Checked: 2026-09-25

Purpose: define which data can be collected without adding a new paid service.

## Classification

- **A — Free production candidate:** official source, automation path is documented or ordinary public access is suitable, provenance can be preserved.
- **B — Free research/provisional:** useful for experiments, but not sufficient by itself for final PIT production evidence.
- **C — Paid / gated:** excluded from the current no-new-paid-services path.

## KAP public website — A/B depending workload

Observed capabilities:

- public disclosure search
- exact disclosure send date/time on search results
- financial-report downloads by company/year/period
- historical year selector visible back to 2009
- company/fund detail pages
- corporate-action and disclosure pages

Use in Zincir Kıran:

- publication timestamps
- financial reports
- disclosure metadata
- corporate-action evidence
- issuer/security identity evidence
- revision/correction discovery

Important limitation:

KAP's official high-volume Data Publishing Service REST API is a subscriber integration. Official documentation states that subscribers must first sign a Borsa İstanbul data-distribution agreement, receive authorization from MKK and use an API key/IP authorization. It also says high-intensity requests for KAP-site data should use the API service after the required procedures.

Therefore:

- normal public-page/manual/download research is allowed as the current free path
- we do **not** design an aggressive high-volume scraper around the public website
- the gated REST API is **C** and disabled for now

Current status: **A for authoritative evidence and limited/prospective collection; not yet a free high-volume historical API.**

## Borsa İstanbul public Daily Bulletin — A for prospective collection

Official public pages expose:

- Daily Bulletin
- Equity Market bulletin data
- current/public file paths and bulletin interfaces
- some market/company datasets

Borsa İstanbul also states that historical Borsa İstanbul data are available through DataStore and that various older files were removed from the public website.

Use in Zincir Kıran:

- collect official daily market/bulletin snapshots prospectively
- hash and archive each retrieved file through `raw_records`
- preserve retrieval timestamp and source URL
- cross-check corporate-action / market-state data

Current status: **A for prospective official daily collection.**

## Borsa İstanbul DataStore — C

Role:

- official historical/reference-data route
- potentially valuable for deep history, delistings, identifiers and market data

Reason disabled:

- historical data sales / contractual route
- user requested no new paid services

Current status: **C — do not use or purchase.**

## TCMB EVDS — A

Official documentation states:

- EVDS provides REST/web-service access
- data can be returned as JSON/CSV/XML
- API use requires a registered user/API key
- EVDS services, including registered-user use, are offered free of charge

Use in Zincir Kıran:

- FX
- policy / market interest-rate series
- monetary and liquidity series
- inflation-related macro series where available
- later regime-model inputs

Rules:

- API key stays in environment variables only
- raw response is hashed/stored before normalization
- observation/revision metadata are preserved when available

Current status: **A — free production candidate for macro/regime data.**

## Yahoo Finance BIST (.IS tickers) — B

Verified examples such as `AKBNK.IS` and `THYAO.IS` expose:

- daily Open / High / Low / Close
- Adjusted Close
- Volume
- TRY-denominated historical observations

Use in Zincir Kıran:

- fast research baseline
- temporary price-history experiments
- cross-checking

Critical limitations:

- not an official Borsa İstanbul source
- delisted-security coverage is not established
- survivorship completeness is not established
- adjustment/revision semantics must not be assumed PIT-safe
- provider terms and stable programmatic-access rules must be respected

Current status: **B — research/provisional only; never the sole production price source.**

## InvestingPro+ — B / existing subscription only

The user already has InvestingPro+.

Use:

- manual/authenticated cross-check
- field discovery
- historical fundamentals/ratios where visibly available
- analyst estimates/revisions exploration

Rules:

- do not buy an additional data product
- do not assume InvestingPro history is point-in-time
- do not replace KAP raw facts with derived ratios
- automated extraction is not assumed permitted

Current status: **B — enrichment/cross-check.**

## Current no-paid ingestion plan

### Fundamentals / disclosures

Primary: KAP public evidence.

### Official prospective market data

Primary: Borsa İstanbul public Daily Bulletin / equity bulletin snapshots.

### Macro / regime

Primary: TCMB EVDS.

### Historical prices for early research only

Temporary: Yahoo Finance `.IS` coverage, clearly marked `PROVISIONAL`.

### Historical official deep backtest

Blocked until one of these occurs:

1. a genuinely free, legally usable, sufficiently complete source is validated,
2. historical files already owned by the user are imported,
3. the user later chooses to license official historical data.

No production result may hide this limitation.

## Data-quality gate

Every source adapter must write at least:

```text
source_id
batch_id
source_record_key
source_url
content_sha256
source_published_at
retrieved_at
raw payload or storage_uri
```

before a normalized PIT fact is allowed to exist.
