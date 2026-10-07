# Historical Liquidity / Capacity Robustness — Result

Implementation 39 ran successfully on GitHub Actions run **37663645104**.

Artifact: **11501163693**  
Digest: `sha256:65828f56800184c582ddbc45876cc620ea4884752f6b832612d65c5aff1ff8d0`

The preregistered capacity grid was not changed after results.

## Data coverage

The verified daily market corpus produced:

- **271,267** daily Close/Volume rows;
- **258,309** valid 63-observation ADV rows;
- exact source SHA256 preserved;
- **zero missing ADV signal dates** across every tested contender/horizon;
- selected-name dated ADV coverage = **100%**.

This closes the immediate evidence-coverage question for historical BIST100-member
capacity research in the covered period.

## Strictest pre-registered scenario: 1% participation / 1 execution day

| Horizon | Contender | Missing ADV dates | Selected ADV coverage | Mean fold median capacity | Worst observed capacity | TRY 10m support | TRY 25m support |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H20 | HIGH_52W_PROXIMITY | 0 | 100.0% | 25.9m TL | 6.5m TL | 95.2% | 51.9% |
| H20 | EW5_COMPOSITE | 0 | 100.0% | 25.1m TL | 9.3m TL | 95.2% | 47.6% |
| H20 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0 | 100.0% | 25.0m TL | 9.3m TL | 97.6% | 40.0% |
| H60 | HIGH_52W_PROXIMITY | 0 | 100.0% | 28.0m TL | 6.5m TL | 91.7% | 66.7% |
| H60 | EW5_COMPOSITE | 0 | 100.0% | 26.5m TL | 11.7m TL | 100.0% | 58.3% |
| H60 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0 | 100.0% | 27.2m TL | 11.7m TL | 100.0% | 58.3% |
| H120 | HIGH_52W_PROXIMITY | 0 | 100.0% | 26.1m TL | 7.3m TL | 94.4% | 55.6% |
| H120 | EW5_COMPOSITE | 0 | 100.0% | 25.0m TL | 11.7m TL | 100.0% | 55.6% |
| H120 | TRAIN_ONLY_EVIDENCE_WEIGHTED_5F | 0 | 100.0% | 22.8m TL | 11.7m TL | 100.0% | 33.3% |

The strictest scenario already shows the economically important boundary:

- TRY **1m** and **5m** are supported on every tested H20-H120 signal date.
- TRY **10m** is supported on essentially all H20-H120 dates.
- TRY **25m** is only partially supported under 1% / 1 day.
- TRY **50m** is rarely supported under 1% / 1 day.

So capacity is not currently a data-coverage problem, but it becomes a real
portfolio-design constraint as capital increases.

## Scenario scaling

Because the capacity rule is linear in participation rate and execution days,
the preregistered grid behaves as expected.

For H20 mean fold median capacity:

- 52W High: 25.9m TL at 1%/1d; 129.5m TL at 5%/1d.
- EW5: 25.1m TL at 1%/1d; 125.3m TL at 5%/1d.
- Dynamic: 25.0m TL at 1%/1d; 124.9m TL at 5%/1d.

H60 and H120 show a similar scale: roughly **23–28m TL** median capacity at
1%/1d and roughly **114–140m TL** at 5%/1d.

These numbers are not recommended portfolio sizes. They are sensitivity
evidence.

## Contender interpretation

Capacity does not overturn the signal conclusions from Implementation 38.

- 52W High has higher turnover, but its historical liquidity is sufficient that
  this does not create an obvious capacity failure in the tested BIST100 period.
- EW5 generally has lower turnover and comparable or slightly better worst-case
  capacity in several horizons.
- Dynamic remains viable from a pure ADV-capacity perspective; its weaker
  H20/H60 long-leg results were not caused by missing liquidity evidence.

This is important: **the dynamic challenger's weaker portfolio evidence cannot
be explained away as a simple illiquidity artifact.**

## Decision

Do not choose a production participation rate, execution window, liquidity
cutoff, or portfolio notional from this result.

Implementation 39 establishes:

1. historical ADV evidence is complete for the tested portfolios;
2. small portfolio sizes are comfortably feasible within the sensitivity grid;
3. capacity starts to matter around larger portfolio notionals under the
   strictest scenario;
4. no contender earns production promotion from capacity evidence alone.

The result remains `EXPERIMENTAL_VERSION_RISK`.

Yahoo-derived daily volume is validated derived market data, not official Borsa
daily truth. No historical bid/ask, slippage, or market-impact series was
invented.
