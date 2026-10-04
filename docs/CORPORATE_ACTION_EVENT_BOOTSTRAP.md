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


## Detail subtype materialization

A bounded real KAP sample proves that some subject/summary pairs support more specific subtype labels:

- disclosure 1176724, CIMSA — summary: `İç Kaynaklardan Bedelsiz Sermaye Artırımı`
  → BONUS_ISSUE_DISCLOSURE
- disclosure 1176183, SUNTK — summary: `Bedelsiz Sermaye Artırımına İlişkin SPK Başvurusu`
  → BONUS_ISSUE_DISCLOSURE
- disclosure 1176343, MEDTR — summary: `Bedelli Sermaye Arttırımından Elde Edilecek Fonun Kullanımına İlişkin Rapor`
  → RIGHTS_ISSUE_DISCLOSURE
- disclosure 1176748, HUBVC — subject: `Kar Payı Dağıtım İşlemlerine İlişkin Bildirim`
  → DIVIDEND_PROCESS_DISCLOSURE

The source window is 2023-07-23..2023-07-29 and its response SHA256 is
`4cc0568d14b2d9150eff519be89f16813971eab6e618f7dcca27cbc86d7be3c5`.

These labels classify the disclosure/process only. They do not create:
- bonus/rights ratios
- ex-date
- payment date
- record date
- cash dividend amount

A dividend-process disclosure therefore does not map directly to a CASH_DIVIDEND event until amount/date detail is acquired.
