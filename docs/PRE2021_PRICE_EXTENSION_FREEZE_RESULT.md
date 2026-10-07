# Pre-2021 Historical Price Extension — Freeze Result

Implementation 42C successfully converted the live 42B recoverability audit into
a frozen research data package.

Freeze workflow: **37686387496**  
Artifact: **11511291939**  
Artifact digest:
`sha256:13878964230d4956eb7b12cbf274d82255070927e0963df6aa2c2c412c7e92d6`

Frozen package commit:

`9bec14cd18a6b9f521c0a77b4dedf8ed4d5b6438`

## Frozen price corpus

- daily rows: **148,578**
- canonical historical tickers: **127**
- direct Yahoo tickers: **123**
- official-lineage alias tickers: **4**
- deterministic gzip SHA256:
  `e0894027610988651d9ffec6cb53cad5bcfc41ae7dbd132d5e55af06c7afcf5e`

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


## Vendor replay drift and freeze policy

A second coverage-only capture was intentionally observed before any H252 alpha
result was opened. It returned the same row count and the same 11/11 acceptance
profile, but the historical price bytes differed:

- first capture SHA256:
  `57a16c08cee591acf18ba9955b45b5e1deba9cea784bb70c49a7c5e2f16cb2bd`
- second capture SHA256:
  `e0894027610988651d9ffec6cb53cad5bcfc41ae7dbd132d5e55af06c7afcf5e`

This demonstrates that a live vendor replay is not an immutable research
source, even over a historical date range.

The **second capture is therefore the canonical V1 freeze**. CI no longer
downloads Yahoo history. It only verifies exact committed hashes. Any future
refresh must create a new dataset/version rather than silently rewrite V1.
