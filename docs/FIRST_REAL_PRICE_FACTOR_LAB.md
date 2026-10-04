# First Real Price Factor Lab

This PR runs a diagnostic-only real BIST100 price-factor study.

Locked inputs:
- 271,267-row historical member OHLC/Adj Close/Volume corpus
- 6,000-row historical monthly BIST100 membership/execution panel
- XU100 benchmark closes

Locked factors:
- MOM_12_1
- MOM_6_1
- HIGH_52W_PROXIMITY
- LOW_VOL_63D
- LIQUIDITY_63D

Locked horizons:
- H20
- H60
- H120
- H252

Outputs are diagnostic only and cannot be used as a production-readiness claim.
