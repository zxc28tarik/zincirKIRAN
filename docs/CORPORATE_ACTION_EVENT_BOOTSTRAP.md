# Corporate Action Event Bootstrap

Source evidence is inherited from the verified Total Rasyo KAP adaptive inventory.

## Proven inventory coverage

- 2016-05-01 through 2026-07-31
- 595 successful adaptive windows
- 0 failed windows
- 0 unsplittable 2,000-row cap hits
- 649,244 total disclosure rows
- 132,668 rows where `disclosureType == CA`
- capture manifest SHA256:
  `1935232295360b1026a036e725809e0e73a62253ce07145bbc1f13fd6abd1345`

The W6 fail-closed audit then used subject markers that could indicate a share-count change and found:

- 11,680 positive action events
- 699 distinct tickers
- all 60 historical cutoffs had reachable corporate-action coverage

## Typed bootstrap scope

Supported positive-event classifications:

- CAPITAL_INCREASE
- CAPITAL_DECREASE
- MERGER
- DEMERGER
- SHARE_CLASS_CHANGE
- AMBIGUOUS_SHARE_COUNT_ACTION

Ticker changes use the separately verified official Borsa ticker-lineage source.

## Important boundary

The 11,680-event count is **not** a complete dividend/split catalog.

The source audit deliberately used a broad, fail-closed subject filter for share-count-risk detection. Therefore:

- original KAP subject text is preserved;
- no capital ratio, entitlement ratio, ex-date, payment date, or share amount is invented;
- a subject containing multiple supported markers becomes AMBIGUOUS_SHARE_COUNT_ACTION;
- CAPITAL_INCREASE is not automatically called BONUS_ISSUE or RIGHTS_ISSUE without detail evidence;
- dividend coverage remains a separate acquisition/materialization task.

## Positive events vs absence

A later-captured historical KAP disclosure can prove that a positive event existed.

A claim that **no** share-count event existed in an interval is allowed only when the entire interval is covered by the gap-free adaptive inventory. Incomplete windows never become absence evidence.
