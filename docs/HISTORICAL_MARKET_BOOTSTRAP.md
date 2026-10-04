# Historical Market Bootstrap from Total Rasyo

Zincir Kıran can reuse the validated V24 historical price corpus from TOTAL-RASYO-HESAPLAYICI.

## Daily stock-price corpus

Source commit:
`883e680a2564e38f4c08a21bc88aa95b8f164036`

Artifact:
`data/backtest_sources/yahoo_resolved/historical_member_prices_resolved_2020-07_2026-08.csv.gz`

SHA256:
`b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141`

Evidence:
- 270,038 direct Yahoo rows
- 271,267 resolved rows after official Borsa ticker-lineage mapping
- no date shifting
- no forward fill
- old-code alias rows only before official effective code-change dates

Authority:
**VALIDATED_DERIVED_MARKET_DATA**

This dataset is usable for Zincir Kıran research/backtest in its covered universe/date scope, but it must never be relabeled as official Borsa daily stock data.

## Monthly BIST100 execution-price panel

Artifact:
`data/backtest_sources/yahoo_resolved/monthly_member_signal_price_coverage.csv`

SHA256:
`a3b14014aa4d3ff16a082bc0dac64346b906f4b7720aeae5a8c449a2add314f2`

Coverage:
- 60 signal months
- 100 BIST100 members per month
- 6,000 / 6,000 exact signal-day price rows
- 5,988 Yahoo/lineage rows
- 12 official Borsa İstanbul THB supplements
- zero remaining execution-price gaps

Authority:
**VALIDATED_EXECUTION_PANEL**

## THB official supplements

The 12 exact gaps were filled from official Borsa İstanbul Equity Market Daily Bulletin archives. The proof retains:
- exact official archive URL
- archive SHA256
- member CSV SHA256
- bilingual Turkish/English schema verification
- exact OPENING PRICE / CLOSING PRICE field semantics

These 12 source rows are official Borsa evidence; the rest of the daily Yahoo-derived corpus is not.

## What this closes

This substantially reduces the need for InvestingPro export for:
- 2020-07..2026-08 historical BIST100-member daily OHLC / adjusted-close / volume data within the frozen member corpus
- 2021-08..2026-07 monthly BIST100 signal-day execution prices

## What remains open

- all-BIST, not only historical BIST100-member scope
- all-BIST historical daily volume outside the historical BIST100-member corpus
- official Borsa full daily stock-price package if we later require official-only production evidence
- corporate-action-aware adjusted-return reconstruction for each use case

InvestingPro+ should now be prioritized for fundamentals, estimates/revisions, broader all-BIST coverage and any missing volume data rather than duplicating this already validated price corpus.
