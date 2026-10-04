# Current BIST Roster / Share-State Bootstrap

This package is for current roster reconciliation and future Live Shadow inputs.

## Current KAP roster

- 807 rows
- source: KAP public BIST companies page
- captured 2026-09-16
- exact CSV SHA256 locked

Important: this is not automatically the investable equity universe. The KAP roster can contain multiple ticker/instrument codes tied to the same issuer. It is therefore **CURRENT_ROSTER_DISCOVERY_ONLY**.

## Current explicit share basis

Total Rasyo captured 807 roster rows / 756 unique issuers and produced 528 usable single-ticker explicit share-basis rows.

Economic rule:
`sum(class_nominal_value / explicit_class_nominal_value_per_share)`

This is valuable for:
- market-cap reconciliation
- dilution/share-state checks
- validating InvestingPro Shares Outstanding
- current Live Shadow

It is **not historical PIT evidence**.

## Current raw close

- 629 usable current raw Close rows
- auto_adjust=false
- adjusted close is diagnostic only
- 178 explicit rejections

This is a **CURRENT_MARKET_SNAPSHOT**, not historical data.

## InvestingPro impact

When the InvestingPro screener export arrives, reconcile it against the 807-row KAP roster rather than trusting one source blindly:
- ticker present in both
- issuer/company-name match
- primary trading item selection
- duplicate/multiple instrument codes
- shares outstanding versus explicit KAP share basis
- price versus current raw-close snapshot

Current artifacts must never be copied backward into historical model dates.
