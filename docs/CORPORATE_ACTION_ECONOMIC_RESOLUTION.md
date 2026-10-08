# Corporate-Action Economic Resolution Ladder

Implementation 45F is the next step after 45E showed that event-absence
screening leaves **zero** current HIGH_52W inputs ready.

The response is not to narrow the classifier after seeing that result.

Instead, 45F resolves event evidence explicitly.

## Resolution hierarchy

A classified event can release its risk only through official detail evidence.

### Official economic action resolved

Requires enough official KAP/Borsa detail to materialize the economic event.

Dividend examples require authoritative dates and cash economics.

Share-multiplier / bonus / split / rights events require authoritative
effective mechanics.

### Official non-price-affecting process resolved

Allowed only when official detail explicitly establishes that the listed
security's price/share continuity is unaffected.

Subject text such as "merger" is never enough by itself.

### Vendor corroborated only

Yahoo Dividends / Stock Splits and Adj Close-to-Close adjustment-factor changes
are useful corroboration.

They **cannot release an event risk alone**.

### Unresolved / conflict

Missing detail, insufficient detail or source conflict remains blocked.

## Locked action contracts

### Cash dividend v1

Pure-cash resolution requires an exact listed ticker/share-group match plus
official KAP evidence for TRY currency, finalized ex/hak-kullanim date, gross
cash per 1 TL nominal share, payment date, and an explicit zero share-dividend
component. Proposed dates and vendor-only evidence cannot resolve risk.

### Share multiplier v1

Bonus/split-style share-multiplier resolution requires:

- exact listed ticker/share-group match exactly once;
- finalized effective/ex/hak-kullanim date; and
- either an explicit non-unit share multiplier or a positive official
  bonus-rate mechanic.

A unit multiplier with no positive bonus mechanic is insufficient. Proposed
dates are insufficient. Yahoo Stock Splits may corroborate but can never
satisfy this contract alone. Rights issues remain a separate contract because
subscription price, entitlement ratio and rights-use dates change the economic
mechanics.

The contract evaluator returns deterministic reason codes and remains separate
from the generic resolution ladder. No event is promoted merely because a
vendor action exists or because the subject line resembles a bonus/split.

## KAP detail structure

A frozen KAP detail-page sample confirms that current KAP pages server-render
their disclosure payload into Next.js data. The page contains:

- `disclosureBasic` metadata including disclosureIndex/title/publishDate;
- a server-rendered `disclosureBody`;
- explicit taxonomy field names and values.

45F captures the raw page bytes and parses only these explicit fields. It does
not infer economic values from prose when a structured field is absent.

## Scope

The merged 45D + 45E risk inventory contains:

- **411 ticker-event risk rows**
- **400 unique KAP disclosure IDs**
- **99 affected current tickers**

Unique disclosure types:

- 231 dividend-process
- 76 capital-increase
- 33 bonus-issue
- 23 rights-issue
- 32 merger
- 5 demerger

Each KAP page is captured once per unique event.

No score or real shadow run is created in 45F.
