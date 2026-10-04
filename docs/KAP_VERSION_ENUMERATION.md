# Historical Financial Version Enumeration

This implementation narrows the largest remaining historical-financial PIT risk.

## Proven problem

Total Rasyo W10/P7 established that current KAP bulk financial archives are not version-complete historical snapshots.

One proven chain:

- older disclosure: **1122417**, published 2023-03-09 18:36:13 +03
- newer disclosure: **1126845**, published 2023-03-21 18:32:11 +03
- relation: **Düzeltilmiş Bildirim**

The preserved annual bulk archive contained only the newer report. Four of 437 compared numeric slots changed, including a parent/non-controlling-interest swap. Backfilling the newer values before 2023-03-21 would therefore create look-ahead.

## Public KAP query route

Official route:

`https://kap.org.tr/tr/api/disclosure/members/byCriteria`

A captured March 2023 query returned:
- 423 financial-report disclosures
- 19 correction/supersession markers
- 9 rows marked superseded
- HTTP 200
- response SHA256 `29bb3d7bd3bef0e07c4a1855416751b85ba61affc2d04e973873a16a59f69305`

This proves historical superseded rows can still be exposed by the public endpoint years later.

It does **not** prove completeness.

## Zincir Kıran enumeration plan

The initial research plan enumerates 60 half-open monthly publication windows:

- first: 2021-08-01 .. 2021-09-01
- last: 2026-07-01 .. 2026-08-01

For each window we retain:
- exact request payload
- exact response bytes/hash
- HTTP status
- disclosure id
- publication timestamp
- ticker codes
- report year/period
- correction/supersession marker
- correction-chain edges when exposed

## Mandatory limitation

Even if all 60 windows succeed, the catalog is **not authoritative-complete** unless KAP or another official source provides a retention/completeness guarantee.

Allowed outputs:
- ENUMERATION_NOT_RUN
- ENUMERATED_PARTIAL
- ENUMERATED_WITH_CORRECTION_CHAINS

Forbidden interpretation:
- “all historical versions are proven complete”

This catalog is still very useful: it identifies known revisions and allows Zincir Kıran to reject or time-bound affected financial facts rather than blindly trusting the latest bulk archive.
