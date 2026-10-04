# Official Source Acquisition Runbook

This runbook starts the real-evidence phase. Test fixtures never count as evidence.

## Priority 1 — Borsa İstanbul

Landing surface:
- https://www.borsaistanbul.com/veriler/pay-piyasasi-verileri

Verified public surface notes:
- The Pay Piyasası page exposes bulletin/market/reference file selectors.
- The page publishes a `DataFilePaths.zip` link describing file/directory paths.
- The page explicitly points broader historical-data access to Borsa İstanbul DataStore.
- Current/reference items include first trading dates/prices and closed trading lines.

Acquisition policy:
1. Acquire public downloadable files only from exact official URLs discovered from the official path manifest/page.
2. Preserve exact bytes, URL, retrieval time, media type and SHA-256.
3. Do not invent undocumented URL patterns.
4. If the historical range needed for research is available only through DataStore, record that as a blocker/paid-data decision instead of scraping around it.

## Priority 2 — KAP

Landing/search surfaces:
- https://kap.org.tr/tr/bildirim-sorgu
- https://kap.org.tr/tr/beklenen-bildirim-sorgu

Verified public surface notes:
- KAP exposes detailed disclosure search.
- KAP exposes financial-statement item search.
- Financial reports are a first-class disclosure category.
- Publication/disclosure timing must be retained for PIT use.

Acquisition policy:
1. Prefer official disclosure/search/export paths.
2. Preserve publication timestamp and retrieval timestamp separately.
3. Preserve original attachments/files whenever available.
4. Never use a later restated financial value as though it were known before its publication.

## First source audit result

As of 2026-10-04, the acquisition layer is ready, but a complete historical BIST research package has **not** been acquired inside the repository.

Current blocker state:
- Borsa İstanbul public pages are confirmed and their file-path manifest link is identified.
- Broader historical market data is explicitly routed by Borsa İstanbul to DataStore.
- KAP public search surfaces are confirmed, but a stable automated export endpoint is not yet locked into code.
- Therefore the first real research snapshot must remain **BLOCKED_WITH_GAPS** until actual raw artifacts are downloaded and passed through Implementation 16.

This is intentional. A blocker receipt is preferable to fabricated PIT coverage.
