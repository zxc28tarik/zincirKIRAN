# Pre-2021 Price + Fundamental Coverage / H252 Power Audit

Implementation 42B is a **coverage-only** step under parent issue #104.

Implementation 42A solved historical BIST100 membership. 42B asks whether the
data needed by the current five-factor research stack actually exists far
enough back to create more independent H252 validation folds.

## No performance peeking

This implementation does **not** compute:

- IC;
- long-leg return;
- Q5-Q1 spread;
- model coefficients;
- portfolio performance;
- champion decisions.

It measures only data and protocol eligibility.

## Market evidence audit

Historical member prices are discovered from Yahoo Finance using the historical
BIST trading code directly:

`<ticker>.IS`

Window:

- stock discovery: 2018-01-01 through 2022-08-31;
- XU100 calendar: 2018-01-01 through 2026-08-31.

No missing historical ticker is automatically replaced with a current symbol.
Known lineage/merger candidates are reported separately and require explicit
identity evidence before they may enter a later frozen dataset.

For every reconstructed monthly BIST100 cell the audit records whether it has:

- exact signal-day price;
- 252 stock observations for 52-week-high proximity;
- 6-1 momentum lookback;
- 63-day low-volatility lookback;
- ADV63;
- exact stock price on the XU100 trading date 252 sessions after the signal.

## Fundamental evidence audit

The exact existing semantic corpus and hashes are reused. No new KAP facts are
downloaded into the research corpus.

For each historical member/date, the existing PIT materializer is asked whether
it can produce:

- `gross_margin_acceleration`;
- `operating_margin_acceleration`.

Unavailable remains unavailable.

## Five-factor mechanical eligibility

The audit then performs the same broad-sector neutralization rule used by the
real Factor Lab:

- date-valid sector route;
- minimum five names in a sector/factor group;
- percentile rank minus 0.5.

A row is mechanically five-factor eligible only if all five sector-neutral
scores exist:

1. HIGH_52W_PROXIMITY
2. LOW_VOL_63D
3. MOM_6_1
4. operating_margin_acceleration
5. gross_margin_acceleration

A signal month is mechanically H252-testable only when at least 20 such rows
also have an exact H252 future-label price endpoint.

## Power calculation

Before any alpha result is recomputed, the audit combines eligible pre-2021
months with the already validated 60-month common-panel date range and applies
the existing maturity-purge / validation-embargo block builder.

It reports:

- current expected H252 folds (sanity check: should reproduce one);
- extended expected H252 folds;
- the additional validation blocks created by usable earlier history.

This determines whether further data acquisition is worth doing before any
performance test is opened.


## Protocol amendment A1 — frozen-calendar sanity

The first coverage-only workflow revealed a protocol mismatch before any alpha
performance was opened: applying a refreshed live Yahoo XU100 calendar to the
existing 60-month period mechanically produced two H252 validation blocks,
whereas Implementation 35 on the frozen research data produced one.

That is not accepted as "new power." The existing-period baseline must remain
on the same frozen XU100 calendar used by the validated research stack.

The audit therefore now:

1. uses the frozen M3 XU100 calendar for the existing research period;
2. uses live Yahoo XU100 dates only before the frozen calendar begins;
3. splices the two calendars at the frozen minimum date;
4. fails closed unless the current 60-month baseline reproduces exactly **one**
   H252 fold.

This amendment changes no factor, score, target, threshold, or performance
result. It is solely a data-authority/sanity correction made before any H252
alpha rerun.
