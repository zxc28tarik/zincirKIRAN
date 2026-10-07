# Freeze Pre-2021 Historical Price Extension

Implementation 42C converts the live recoverability evidence from 42B into a
reusable, hash-pinned research price package.

## Target

Only the eleven mechanically useful pre-anchor signal months are targeted:

- 2020-09 through 2021-07.

Prices are fetched from 2018-01-01 through 2022-08-31 so the package can support
both 252-session factor lookback and H252 forward endpoints.

## Ticker identity

Direct historical BIST code is always attempted first.

If Yahoo no longer exposes the old symbol, aliasing is allowed only for explicit
code changes present in the frozen official Borsa İstanbul code-change source
already used by Total Rasyo:

- DGKLB → DGNMO
- ITTFH → LRSHO
- IPEKE → TRENJ
- KERVT → BESLR
- KOZAA → TRMET
- KOZAL → TRALT

These are identity/code changes, not merger guesses.

The following are deliberately **not** auto-aliased in 42C:

- GUSGR → TURSG
- ADANA → OYAKC
- ANACM / SODA / TRKCM → SISE

Those require a stronger event-specific conversion treatment if ever needed.

## Determinism

The workflow freezes:

- canonical daily OHLC / Adj Close / Volume;
- exact 11-month historical membership;
- signal-date price coverage;
- unresolved ticker/cell audit;
- provenance JSON;
- SHA256SUMS.

Canonical rows are sorted by ticker/date. Gzip uses mtime=0 so the byte hash is
stable for the same source rows.

No performance statistic is computed in this implementation.
