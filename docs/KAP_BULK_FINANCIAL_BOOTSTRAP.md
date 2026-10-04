# KAP Bulk Financial Archive Bootstrap

Zincir Kıran can reuse the real KAP bulk financial archives already acquired and audited in TOTAL-RASYO-HESAPLAYICI.

## Coverage

- 28 official KAP ZIP archives
- 2019 9A through 2026 6A
- official route pattern:
  `https://kap.org.tr/tr/api/financialTable/download/{year}/{period_code}`
- exact observed SHA256, member count and byte size per archive
- all downloads succeeded in the source evidence run

## What this gives us

These archives are valuable raw financial evidence and are enough to avoid rediscovering:
- KAP bulk download routes
- archive identities
- archive member counts
- archive byte hashes
- large portions of historical financial schema

The source project's semantic evidence additionally scanned all 28 archives and found:
- 994 matched insurance/finance reports
- 71 source entities
- 917 exact role/row/label identities
- 10 technical roles

## What this does NOT give us

The current bulk archive for a historical quarter can contain a later version of a filing than what an investor knew at the original date.

That is not theoretical: in the source reacquisition receipt:
- 2025 annual archive drifted from the earlier manifest;
- 2026 6A archive drifted from the earlier manifest.

Therefore a current KAP bulk ZIP is **RAW_EVIDENCE**, not automatically a historical point-in-time snapshot.

Until superseded-version enumeration / original publication version history is solved:
- authoritative historical PIT claim = forbidden
- PIT materialization = not authorized
- forward-return model training must not assume these archives were known in their current form at historical cutoffs

## Practical use now

Use this package for:
- schema discovery
- semantic mapping
- raw quarterly financial values
- company/report inventory
- cross-checking InvestingPro exports
- identifying where exact historical disclosure/version retrieval is still needed

Do not use it to backfill revised financial values into dates before those revisions were published.
