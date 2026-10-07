# Official BIST100 Membership Backcast 2019–2021

Implementation 42A is a data-evidence step under parent issue #104.

It reconstructs historical BIST100 membership backwards from the independently
validated **2021-08-02** 100-name execution-panel anchor.

## Why periodic announcements were not enough

Quarterly Borsa İstanbul constituent announcements correctly reconstruct most
of the chain, but a live index can change inside a quarter.

Three events are required for exact round-trip consistency:

- **2021-06-16 — BAGFS → ECZYT**: BAGFS moved to Yakın İzleme Pazarı and
  Q2 first reserve ECZYT entered BIST100.
- **2020-09-02 — GUSGR → TURSG**: Güneş Sigorta continued after the
  merger/name-code transition under TURSG.
- **2020-05-21 — ADANA → SARKY**: ADANA left due to the OYAK Cement merger and
  Q2 first reserve SARKY entered.

Without these events the backcast fails closed: expected periodic additions are
missing or member count drifts from 100.

## Validation rules

The reconstruction runner:

1. downloads the pinned Aug-2021 anchor from the exact Total Rasyo commit;
2. verifies its SHA256;
3. requires exactly 100 unique anchor names;
4. reverses every periodic and intra-period event;
5. requires exactly 100 unique names after every reverse step;
6. replays all events forward from the earliest reconstructed state;
7. requires an exact set match to the Aug-2021 anchor.

No current universe is used to infer history.

## Evidence boundary

Periodic events are primary Borsa İstanbul announcement pages.

The three intra-period events are explicitly labeled according to the evidence
available: Borsa-issued KAP event mirrors / KAP indexes / issuer annual-report
corroboration. They are not silently promoted to stronger provenance than the
source actually provides.

This step reconstructs **membership only**. It does not yet solve the H252
power problem, because the existing validated daily price corpus starts in
2020-07 and 52W High itself needs roughly 252 prior trading observations.

Parent issue #104 therefore remains open until price and fundamental history
are extended or otherwise independently acquired.
