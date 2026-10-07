# Pre-2021 Historical Price Extension — Freeze Result

Implementation 42C successfully converted the live 42B recoverability audit into
a frozen research data package.

Freeze workflow: **37686065246**  
Artifact: **11511480842**  
Artifact digest:
`sha256:f71944c036021d304a7106469c4748c8afb942647464dd7c990735f9271a9641`

Frozen package commit:

`32d4d9f8e51124f1be992bb70eee75308e6a8a22`

## Frozen price corpus

- daily rows: **148,578**
- canonical historical tickers: **127**
- direct Yahoo tickers: **123**
- official-lineage alias tickers: **4**
- deterministic gzip SHA256:
  `57a16c08cee591acf18ba9955b45b5e1deba9cea784bb70c49a7c5e2f16cb2bd`

Official-lineage aliases actually used:

- IPEKE
- KERVT
- KOZAA
- KOZAL

## Remaining unresolved identities

The package deliberately leaves these merger / pre-2021 identities unresolved:

- ANACM
- GUSGR
- SODA
- TRKCM

They are not guessed or mapped to a successor company.

## Coverage gate

All **11/11** target months from September 2020 through July 2021 passed the
pre-registered gate.

H252 exact five-factor test cells range from **70 to 79** per month,
well above the required minimum of 20.

By January 2021, exact signal-day prices and H252 endpoints are available for
all 100 index members in the reconstructed universe. Earlier months retain
enough exact common evidence despite unresolved merger identities.

## Identity controls

The package uses the pinned official Borsa İstanbul code-change workbook hash:

`cb5e2fc5ed8bd69b75db7707f0078facc3b900ae14cb51e8f3a286e13cf239b5`

Only explicit old-code → new-code identity changes are eligible for aliasing.
Merger relationships remain separate and unavailable.

## Decision

The pre-2021 market-data extension is now frozen and hash-pinned.

This removes the live-vendor dependency that existed in Implementation 42B for
the additional H252 fold. It is now appropriate to construct an **extended
H252 research panel**.

No IC, return, long-leg, ML, cost, portfolio, or champion result was opened in
42C. Parent issue #104 remains open until the extended H252 evidence itself is
evaluated.
