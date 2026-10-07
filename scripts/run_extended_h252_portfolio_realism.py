#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_extended_h252_tournament as ext  # noqa: E402
import run_first_equal_weight_multifactor_challenger as ew  # noqa: E402
import run_historical_liquidity_capacity as cap  # noqa: E402
import run_ml_portfolio_cost_capacity as mp  # noqa: E402

HORIZON = 252
TOLERANCE = 1e-12

EXPECTED = {
    "HIGH_52W_PROXIMITY": {
        "gross": 0.05878220895721851,
        "turnover": 0.7180555555555553,
        "net_25bps": 0.05698707006832963,
        "median_capacity_p1_d1": 21785989.061944336,
    },
    "EW5_COMPOSITE": {
        "gross": 0.06133867529540108,
        "turnover": 0.6138888888888888,
        "net_25bps": 0.059803953073178866,
        "median_capacity_p1_d1": 20397439.5384669,
    },
    "TRAIN_ONLY_EVIDENCE_WEIGHTED_5F": {
        "gross": 0.02083726477848913,
        "turnover": 0.6319444444444443,
        "net_25bps": 0.019257403667378017,
        "median_capacity_p1_d1": 20580780.518259287,
    },
    "FIXED_RIDGE_5F": {
        "gross": 0.08184526256027495,
        "turnover": 0.5499999999999998,
        "net_25bps": 0.08047026256027495,
        "median_capacity_p1_d1": 14414090.14703806,
    },
}


def assert_close(actual: float | None, expected: float, label: str) -> None:
    if actual is None or not np.isfinite(float(actual)):
        raise RuntimeError(f"sanity metric unavailable: {label}")
    if abs(float(actual) - expected) > TOLERANCE:
        raise RuntimeError(
            f"portfolio sanity mismatch {label}: expected={expected:.17g} "
            f"actual={float(actual):.17g}"
        )


def build_extended_panel(
    calendar: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    original, original_calendar = ew.build_common_panel()
    original["signal_date"] = pd.to_datetime(original["signal_date"]).dt.normalize()

    # The calendar object must be the exact existing frozen calendar.
    if not original_calendar["trade_date"].equals(calendar["trade_date"]):
        raise RuntimeError("calendar mismatch between original and extended builders")

    ext.verify_local_freeze()
    early, early_coverage = ext.build_early_common_panel(calendar)

    required = list(ew.FACTORS) + [ew.COMPOSITE, f"TARGET_{HORIZON}"]
    extended = pd.concat(
        [
            early[["signal_date", "ticker"] + required],
            original[["signal_date", "ticker"] + required],
        ],
        ignore_index=True,
        sort=False,
    )
    extended = extended.sort_values(["signal_date", "ticker"]).reset_index(drop=True)

    if extended.duplicated(["signal_date", "ticker"]).any():
        raise RuntimeError("extended panel contains duplicate signal/ticker rows")
    if extended["signal_date"].nunique() != 71:
        raise RuntimeError(
            f"extended panel must contain 71 signal dates; "
            f"found={extended['signal_date'].nunique()}"
        )
    return extended, {
        "original_rows": int(len(original)),
        "original_signal_dates": int(original["signal_date"].nunique()),
        "early_rows": int(len(early)),
        "early_signal_dates": int(early["signal_date"].nunique()),
        "extended_rows": int(len(extended)),
        "extended_signal_dates": int(extended["signal_date"].nunique()),
        "early_coverage": early_coverage,
    }


def original_sanity(
    calendar: pd.DataFrame,
    adv_map: dict[tuple[pd.Timestamp, str], float],
) -> dict[str, object]:
    original, _ = ew.build_common_panel()
    original["signal_date"] = pd.to_datetime(original["signal_date"]).dt.normalize()
    result = mp.run_horizon(original, calendar, adv_map, HORIZON)

    if result["evaluated_fold_count"] != 1:
        raise RuntimeError(
            f"original H252 portfolio fold count !=1: {result['evaluated_fold_count']}"
        )

    for contender, expected in EXPECTED.items():
        observed = result["aggregates"][contender]
        assert_close(
            observed["mean_fold_gross_forward_excess_proxy"],
            expected["gross"],
            f"{contender}.gross",
        )
        assert_close(
            observed["mean_fold_gross_turnover"],
            expected["turnover"],
            f"{contender}.turnover",
        )
        assert_close(
            observed["cost_scenarios"]["25bps"]["mean_fold_net_forward_excess_proxy"],
            expected["net_25bps"],
            f"{contender}.net_25bps",
        )
        assert_close(
            observed["capacity_scenarios"]["p1_d1"]["mean_fold_median_capacity_try"],
            expected["median_capacity_p1_d1"],
            f"{contender}.median_capacity_p1_d1",
        )

    return {
        "pass": True,
        "evaluated_fold_count": result["evaluated_fold_count"],
        "aggregates": result["aggregates"],
    }


def main() -> int:
    # Existing validated daily corpus is sufficient for the 2023-2025
    # validation portfolios; the frozen 42C extension affects training evidence,
    # not the validation-date ADV source.
    adv_map, adv_source = cap.load_adv63()
    _, calendar = ew.build_common_panel()

    sanity = original_sanity(calendar, adv_map)
    extended, panel_receipt = build_extended_panel(calendar)

    result = mp.run_horizon(extended, calendar, adv_map, HORIZON)
    if result["evaluated_fold_count"] != 2:
        raise RuntimeError(
            "extended H252 portfolio realism expected exactly two evaluated folds; "
            f"found={result['evaluated_fold_count']}"
        )

    receipt = {
        "contract": "EXTENDED_H252_PORTFOLIO_REALISM_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "horizon": HORIZON,
        "panel": panel_receipt,
        "original_sanity": sanity,
        "historical_adv_source": adv_source,
        "cost_scenarios_bps": [10.0, 25.0, 50.0],
        "participation_rates": cap.PARTICIPATION_RATES,
        "execution_days": cap.EXECUTION_DAYS,
        "illustrative_notionals_try": cap.NOTIONALS_TRY,
        "extended_result": result,
        "limitations": [
            "This is a forward-return portfolio diagnostic, not a self-financing overlapping-horizon NAV backtest.",
            "Cost bps are sensitivity scenarios, not observed historical execution costs.",
            "ADV capacity uses validated derived market data rather than official Borsa daily volume.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK.",
            "No cost, liquidity, portfolio-size, factor, model or champion setting is optimized from these results."
        ],
    }

    out = ROOT / "research/evidence_runs/extended_h252_portfolio_realism_v1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
