# Data Source Inventory v0.1

Status: preliminary, source-backed reconnaissance  
Checked: 2026-09-25

This document records what has been verified so far. A source is not PIT-safe merely because it contains historical data.

## Decision rules

A production source must be evaluated for:

- exact field coverage
- historical depth
- publication / availability timestamp quality
- revision history
- corporate-action treatment
- survivorship implications
- licensing / reuse constraints
- stable machine access
- source provenance

No historical timestamp may be invented.

## 1. KAP — primary disclosure / publication-time candidate

Official site:

https://kap.org.tr/

Relevant verified surfaces:

- Disclosure query: https://kap.org.tr/tr/bildirim-sorgu
- Financial statement item query: https://kap.org.tr/tr/kalem-karsilastirma
- Example company financial-report query with exact date/time:
  https://kap.org.tr/tr/bildirim-sorgu-sonuc?member=4028e4a140f2ed720140f376bebb01a7&disclosureClass=FR
- Example company profile with year-by-year news downloads:
  https://kap.org.tr/tr/sirket-bilgileri/ozet/1107-turk-hava-yollari-a-o

Observed strengths:

- Financial-report disclosures expose publication date and time.
- Company disclosure history is searchable.
- Company pages expose year-based downloadable disclosure files.
- Financial-report submission schedules are officially published.
- KAP is the authoritative publication venue for listed-company disclosures.

PIT assessment:

**High potential for reported_at / available_at**, subject to historical completeness and extraction validation.

Important caveat:

The financial-statement item comparison page explicitly warns that its information may update with delay and directs users to the main page/search functions for real-time tracking. Therefore we must not assume every KAP surface has identical availability semantics.

Observed API-like URLs such as batch-news downloads are useful discovery signals but are not yet treated as a documented/stable public API contract.

Open verification:

- historical completeness by issuer and disclosure type
- stable identifiers across ticker/name changes
- exact attachment formats for financial statements
- correction / revision linking
- corporate-action disclosure taxonomy
- rate limits / terms for automated extraction

## 2. Borsa İstanbul — primary official market/reference-data candidate

Official market-data page:

https://www.borsaistanbul.com/en/market-data

Official historical-data sales page:

https://www.borsaistanbul.com/en/data/historical-data-sales

DataStore:

https://datastore.borsaistanbul.com/

Verified observations:

- Borsa İstanbul states that historical and some reference data are available through DataStore.
- The official market-data area includes market, equity and company datasets.
- The official market-data page includes information on permanently delisted equities.
- Some historical files moved to DataStore as of 2015-08-01.
- Historical-data access may involve commercial / contractual terms.

PIT assessment:

**Preferred official candidate for price, volume, index/reference and delisting history**, but exact product fields, history depth, costs and licensing must be inspected before acquisition.

Open verification:

- daily OHLCV coverage by security
- total-return / adjustment fields
- corporate-action/reference datasets
- ticker / ISIN history
- index constituent history
- shares / free-float history
- delisting dates and reason codes
- historical market / segment membership
- exact DataStore licensing and redistribution restrictions
- whether revisions/corrections are versioned or only latest-state

## 3. InvestingPro+ — enrichment / cross-check candidate

Public product page:

https://www.investing.com/pro/pricing

Verified public claims include extensive financial metrics, historical data, screening, real-time updates and detailed company research.

Important inconsistency:

Different InvestingPro marketing surfaces describe historical depth / metric counts differently. Therefore public marketing claims are **not** sufficient to establish an exact BIST data contract.

Current role:

- feature discovery
- cross-checking financial statement values
- valuation metrics
- analyst estimates / revisions where available
- derived ratios
- company research
- possible historical metric enrichment

PIT assessment:

**Unverified for primary historical PIT use.**

We must inspect the user's actual BIST coverage inside InvestingPro+ before production use.

Open verification inside authenticated account:

- BIST company universe coverage
- exact fundamental fields
- statement history depth
- historical ratio depth
- analyst estimate / revision history
- shares outstanding / free float
- corporate actions
- whether historical values are point-in-time or retrospectively corrected
- export limits / permitted automated use
- publication timestamps
- source provenance behind derived metrics

Rule:

InvestingPro-derived ratios must not silently replace raw statement facts when raw KAP facts are available.

## 4. Company reports / attachments

Company financial statements and activity reports published through KAP are candidate raw evidence.

Preferred role:

- source-of-truth validation
- revision checks
- accounting-standard metadata
- TMS 29 / inflation-adjustment evidence
- notes needed for sector-specific accounting interpretation

These documents are slower to parse than structured data and should usually support or validate the structured layer rather than become the only ingestion path.

## 5. Initial source hierarchy

This is a provisional evidence hierarchy, not an unconditional precedence rule:

1. KAP / Borsa İstanbul official records
2. company-filed reports and official attachments
3. licensed structured market-data provider
4. InvestingPro+ enrichment / cross-check
5. web extraction with preserved provenance

Conflicts are stored, not silently overwritten.

## 6. Immediate acquisition blockers

Before a valid broad BIST backtest, we still need to solve:

- official or licensed historical OHLCV
- delisted-security historical universe
- corporate-action history
- security identifier / ticker history
- historical shares outstanding / free float where required
- exact KAP publication timestamps at scale
- financial-statement revision lineage
- TMS 29 regime metadata
- source licenses and automated-use constraints

## 7. Next source-validation experiments

1. Select 5 representative issuers:
   - industrial
   - bank
   - insurer
   - GYO
   - holding
2. Reconstruct 8 quarters of financial disclosures from KAP.
3. Preserve original KAP publication timestamps.
4. Compare raw statement facts with InvestingPro+ values.
5. Record all mismatches and revisions.
6. Obtain a sample Borsa İstanbul / DataStore price history and validate corporate actions.
7. Only after this sample passes, scale ingestion to the BIST universe.
