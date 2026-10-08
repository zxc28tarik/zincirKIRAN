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
