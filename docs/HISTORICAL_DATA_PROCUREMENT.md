# Historical Data Procurement Decision — First Actual Dataset

This document locks the procurement route for Zincir Kıran's first actual point-in-time research dataset.

## Verified official-source constraints

### Borsa İstanbul

The official Equity Market Data page states that, as of **2015-08-01**, specified historical data files became available only through **datastore.borsaistanbul.com** and were removed from the public Borsa İstanbul site.

Decision:
- canonical historical price route: **Borsa İstanbul DataStore**
- canonical historical volume route: **Borsa İstanbul DataStore**
- public reference/listing files remain usable where available
- no undocumented URL-pattern reconstruction is allowed

### KAP

KAP exposes public detailed disclosure search and financial-statement query surfaces.

However, KAP's Financial Statement Item Query explicitly states that:
- query results use the latest published current-period values;
- corrections made in prior-period columns are not represented there;
- users needing that detail should use the company's published financial-report disclosure.

Decision:
- canonical financial history: **original KAP financial-report disclosures and attachments**
- canonical availability timestamp: **original KAP disclosure timestamp**
- line-item query: **discovery/cross-check only**, never canonical PIT history

## Domain procurement matrix

| Domain | Canonical route | Access | PIT suitability | Current state |
|---|---|---|---|---|
| Prices | Borsa İstanbul DataStore historical Equity Market data | Paid official | Canonical | BLOCKED_PENDING_ACCESS |
| Volume | Borsa İstanbul DataStore historical Equity Market data | Paid official | Canonical | BLOCKED_PENDING_ACCESS |
| Financials | Original KAP financial-report disclosures/attachments | Free public, acquisition/export work required | Canonical | BLOCKED_PENDING_EXPORT |
| Publication timestamps | KAP disclosure timestamps | Free public | Canonical | ROUTE_LOCKED |
| Corporate actions | Original KAP corporate-action disclosures | Free public | Canonical | ROUTE_LOCKED |
| Universe history | Borsa İstanbul official listing/reference files | Free public | Canonical | ROUTE_LOCKED |

## Explicitly prohibited shortcuts

The first actual dataset must not use any of the following as a silent substitute:

- adjusted-close series without corporate-action provenance;
- future restated financial values backfilled into dates before publication;
- KAP latest line-item comparison view as canonical historical financials;
- NaN/missing data mapped to neutral values;
- survivor-only current-listed universe applied to historical dates;
- vendor exports without timestamp/source provenance.

## Build order

1. Obtain historical raw price/volume package or formal access route from Borsa İstanbul DataStore.
2. Acquire original KAP financial-report disclosure history with disclosure timestamps.
3. Acquire KAP corporate-action history.
4. Build official Borsa İstanbul listing/ticker/delisting history.
5. Hash every raw artifact and register it through Implementation 17 acquisition receipts.
6. Build Implementation 16 PIT snapshot manifests.
7. Produce domain coverage.
8. Run the tournament only after readiness thresholds pass.

## Current decision

The first actual dataset is **not yet buildable to TOURNAMENT_READY** because two canonical domains remain blocked:
- PRICES → Borsa İstanbul DataStore access required.
- VOLUME → Borsa İstanbul DataStore access required.

FINANCIALS additionally remain blocked until original KAP reports can be acquired at historical scale with timestamp provenance.

No paid purchase is authorized by this repository change. This document only records the required route and the reason it is required.
