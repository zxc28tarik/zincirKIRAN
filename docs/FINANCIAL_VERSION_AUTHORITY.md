# Financial Revision / PIT Version Authority

Zincir Kıran must distinguish **a financial value** from **the financial value that was actually public at a historical cutoff**.

## Real KAP regression case

The Total Rasyo P7 hardening work recovered a real superseded KAP version pair for KORTS 2022 annual reporting:

- original disclosure: **1122417**
- original publication: **2023-03-09 18:36:13 +03:00**
- correction disclosure: **1126845**
- correction publication: **2023-03-21 18:32:11 +03:00**
- correction explicitly links the original
- 4 of 437 numeric cells changed
- the later bulk 2022 annual archive retained only the later disclosure

Source P7 receipt SHA256:

`e265681904d80325fca4d23dcc56b4a15ac1f0b7d9a1771d8fe413ada71307b2`

The consequence is direct: using today's bulk archive at a cutoff between 9 March and 21 March 2023 would inject information that did not yet exist.

## Authority classes

### AUTHORITATIVE_PIT

Allowed for strict walk-forward/tournament training only when:
- every relevant disclosure version is enumerated;
- each version has a stable disclosure identity;
- exact publication timestamp is retained;
- immutable raw bytes or an equivalent raw artifact are SHA256-bound;
- version chronology is append-only;
- the chain is known complete for the supported scope.

Cutoff selection is:
`latest version with published_at <= cutoff_at`

### EXPERIMENTAL_VERSION_RISK

Useful for research when version completeness is not proven.

It must:
- remain visibly separate from authoritative results;
- never be silently promoted to production evidence;
- never be mixed into an authoritative tournament as though coverage were equivalent.

### BULK_LATEST_ONLY

A current KAP bulk archive observation where historical superseded versions are not proven.

This is useful raw evidence, but it is **not** authorized as historical PIT factor input.

## Fail-closed rule

If version enumeration is incomplete, the dependent authoritative factor observation is unavailable/rejected. It is not replaced with:
- latest known value;
- neutral score;
- zero;
- interpolated value;
- a later restatement.

## Network/source route boundary

Public KAP notification pages are suitable for low-volume validation and offline snapshot parsing because they expose stable notification IDs, submission timestamps and correction metadata.

At-scale public-site scraping is not treated as an authorized acquisition strategy. The complete authoritative package requires either:
1. official KAP Data Distribution / equivalent authorized service; or
2. an already-acquired immutable historical export/source package with the needed notification/version chronology.
