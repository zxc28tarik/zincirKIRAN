#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_first_equal_weight_multifactor_challenger as ew  # noqa: E402
import run_nested_train_only_evidence_weighted_composite as dyn  # noqa: E402
import run_real_walk_forward_factor_stability as wf  # noqa: E402

CHAMPION = ew.CHAMPION
EW5 = ew.COMPOSITE
DYNAMIC = dyn.DYNAMIC
CONTENDERS = (CHAMPION, EW5, DYNAMIC)
HORIZONS = ew.HORIZONS
COST_BPS = (10.0, 25.0, 50.0)
TOP_FRACTION = 0.20
MIN_CROSS_SECTION = 20


def _gross_turnover(
    previous: dict[str, float],
    current: dict[str, float],
) -> float:
    names = set(previous) | set(current)
    return float(
        sum(abs(current.get(name, 0.0) - previous.get(name, 0.0)) for name in names)
    )


def _portfolio_row(
    group: pd.DataFrame,
    score: pd.Series,
    target_col: str,
    previous: dict[str, float],
) -> tuple[dict[str, object], dict[str, float]] | None:
    work = group[["ticker", target_col]].copy()
    work["score"] = score
    work = work.dropna(subset=["ticker", target_col, "score"])
    if len(work) < MIN_CROSS_SECTION:
        return None

    selected_count = max(1, int(math.ceil(len(work) * TOP_FRACTION)))
    selected = (
        work.sort_values(["score", "ticker"], ascending=[False, True])
        .head(selected_count)
        .copy()
    )
    weight = 1.0 / selected_count
    current = {str(ticker): weight for ticker in selected["ticker"].astype(str)}
    turnover = _gross_turnover(previous, current)
    gross = float(selected[target_col].astype(float).mean())

    net = {
        f"{int(cost)}bps": gross - turnover * cost / 10000.0
        for cost in COST_BPS
    }
    return (
        {
            "cross_section_names": int(len(work)),
            "selected_names": int(selected_count),
            "gross_forward_excess_proxy": gross,
            "gross_turnover": turnover,
            "net_forward_excess_proxy": net,
        },
        current,
    )


def _summarize_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "signal_dates": 0,
            "mean_gross_forward_excess_proxy": None,
            "mean_gross_turnover": None,
            "median_gross_turnover": None,
            "total_gross_turnover": None,
            "mean_selected_names": None,
            "cost_scenarios": {},
        }

    gross = np.array(
        [float(row["gross_forward_excess_proxy"]) for row in rows],
        dtype=float,
    )
    turnover = np.array([float(row["gross_turnover"]) for row in rows], dtype=float)
    selected = np.array([float(row["selected_names"]) for row in rows], dtype=float)

    cost_scenarios: dict[str, object] = {}
    for cost in COST_BPS:
        key = f"{int(cost)}bps"
        vals = np.array(
            [
                float(
                    row["net_forward_excess_proxy"][key]  # type: ignore[index]
                )
                for row in rows
            ],
            dtype=float,
        )
        cost_scenarios[key] = {
            "mean_net_forward_excess_proxy": float(vals.mean()),
            "median_net_forward_excess_proxy": float(np.median(vals)),
            "positive_share": float((vals > 0).mean()),
            "worst_net_forward_excess_proxy": float(vals.min()),
        }

    return {
        "signal_dates": int(len(rows)),
        "mean_gross_forward_excess_proxy": float(gross.mean()),
        "median_gross_forward_excess_proxy": float(np.median(gross)),
        "positive_gross_share": float((gross > 0).mean()),
        "mean_gross_turnover": float(turnover.mean()),
        "median_gross_turnover": float(np.median(turnover)),
        "total_gross_turnover": float(turnover.sum()),
        "mean_selected_names": float(selected.mean()),
        "cost_scenarios": cost_scenarios,
    }


def _aggregate_folds(
    folds: list[dict[str, object]],
    contender: str,
) -> dict[str, object]:
    valid = [
        fold[contender]
        for fold in folds
        if fold.get("status") == "EVALUATED" and contender in fold
    ]
    if not valid:
        return {
            "folds": 0,
            "mean_fold_gross_forward_excess_proxy": None,
            "mean_fold_gross_turnover": None,
            "cost_scenarios": {},
        }

    gross = [
        float(item["mean_gross_forward_excess_proxy"])  # type: ignore[index]
        for item in valid
    ]
    turnover = [
        float(item["mean_gross_turnover"])  # type: ignore[index]
        for item in valid
    ]
    cost_summary: dict[str, object] = {}
    for cost in COST_BPS:
        key = f"{int(cost)}bps"
        vals = [
            float(
                item["cost_scenarios"][key]["mean_net_forward_excess_proxy"]  # type: ignore[index]
            )
            for item in valid
        ]
        cost_summary[key] = {
            "mean_fold_net_forward_excess_proxy": float(np.mean(vals)),
            "worst_fold_net_forward_excess_proxy": float(np.min(vals)),
            "positive_fold_share": float(np.mean(np.asarray(vals) > 0)),
        }

    return {
        "folds": int(len(valid)),
        "mean_fold_gross_forward_excess_proxy": float(np.mean(gross)),
        "worst_fold_gross_forward_excess_proxy": float(np.min(gross)),
        "positive_gross_fold_share": float(np.mean(np.asarray(gross) > 0)),
        "mean_fold_gross_turnover": float(np.mean(turnover)),
        "cost_scenarios": cost_summary,
    }


def _paired(
    folds: list[dict[str, object]],
    left: str,
    right: str,
) -> dict[str, object]:
    gross_diffs: list[float] = []
    cost_diffs: dict[str, list[float]] = {
        f"{int(cost)}bps": [] for cost in COST_BPS
    }

    for fold in folds:
        if fold.get("status") != "EVALUATED":
            continue
        if left not in fold or right not in fold:
            continue
        left_row = fold[left]
        right_row = fold[right]
        gross_diffs.append(
            float(left_row["mean_gross_forward_excess_proxy"])  # type: ignore[index]
            - float(right_row["mean_gross_forward_excess_proxy"])  # type: ignore[index]
        )
        for key in cost_diffs:
            cost_diffs[key].append(
                float(
                    left_row["cost_scenarios"][key]["mean_net_forward_excess_proxy"]  # type: ignore[index]
                )
                - float(
                    right_row["cost_scenarios"][key]["mean_net_forward_excess_proxy"]  # type: ignore[index]
                )
            )

    return {
        "paired_folds": len(gross_diffs),
        "mean_gross_difference": (
            None if not gross_diffs else float(np.mean(gross_diffs))
        ),
        "left_beats_right_gross_fold_share": (
            None
            if not gross_diffs
            else float(np.mean(np.asarray(gross_diffs) > 0))
        ),
        "cost_scenarios": {
            key: {
                "mean_net_difference": (
                    None if not vals else float(np.mean(vals))
                ),
                "left_beats_right_fold_share": (
                    None
                    if not vals
                    else float(np.mean(np.asarray(vals) > 0))
                ),
            }
            for key, vals in cost_diffs.items()
        },
    }


def run_horizon(
    panel: pd.DataFrame,
    calendar: pd.DataFrame,
    horizon: int,
) -> dict[str, object]:
    target = f"TARGET_{horizon}"
    signal_dates = sorted(
        pd.Timestamp(x) for x in panel["signal_date"].dropna().unique()
    )
    maturity = wf.maturity_map(signal_dates, calendar, horizon)
    blocks = wf.validation_blocks(signal_dates, maturity)

    fold_records: list[dict[str, object]] = []
    previous_validation_label_maturity: pd.Timestamp | None = None

    for idx, test_dates in enumerate(blocks, start=1):
        test_start = min(test_dates)
        test_end = max(test_dates)
        if (
            previous_validation_label_maturity is not None
            and test_start <= previous_validation_label_maturity
        ):
            raise RuntimeError("validation embargo violation")

        train_dates = [
            signal
            for signal in signal_dates
            if signal < test_start
            and maturity.get(signal) is not None
            and maturity[signal] < test_start
        ]
        if len(train_dates) < wf.MIN_INITIAL_TRAIN_MONTHS:
            continue

        validation_last_maturity = maturity.get(test_end)
        if validation_last_maturity is None:
            continue

        train_evidence = dyn._factor_train_evidence(panel, horizon, train_dates)
        dynamic_weights = dyn._weights(train_evidence)
        if dynamic_weights is None:
            fold_records.append(
                {
                    "fold_id": f"H{horizon}-F{idx}",
                    "status": "NO_SIGNAL_ZERO_POSITIVE_TRAIN_EVIDENCE",
                    "validation_start": test_start.date().isoformat(),
                    "validation_end": test_end.date().isoformat(),
                    "train_factor_mean_ic": train_evidence,
                }
            )
            previous_validation_label_maturity = validation_last_maturity
            continue

        score_series = {
            CHAMPION: panel[CHAMPION].astype(float),
            EW5: panel[EW5].astype(float),
            DYNAMIC: dyn._score(panel, dynamic_weights),
        }
        rows_by_contender: dict[str, list[dict[str, object]]] = {
            contender: [] for contender in CONTENDERS
        }
        previous_weights: dict[str, dict[str, float]] = {
            contender: {} for contender in CONTENDERS
        }

        for signal_date in test_dates:
            group = panel.loc[panel["signal_date"] == signal_date]
            for contender in CONTENDERS:
                built = _portfolio_row(
                    group,
                    score_series[contender].loc[group.index],
                    target,
                    previous_weights[contender],
                )
                if built is None:
                    continue
                row, current = built
                row["signal_date"] = signal_date.date().isoformat()
                rows_by_contender[contender].append(row)
                previous_weights[contender] = current

        if any(
            len(rows_by_contender[contender]) < wf.MIN_TEST_MONTHS
            for contender in CONTENDERS
        ):
            previous_validation_label_maturity = validation_last_maturity
            continue

        record: dict[str, object] = {
            "fold_id": f"H{horizon}-F{idx}",
            "status": "EVALUATED",
            "train_start": min(train_dates).date().isoformat(),
            "train_end": max(train_dates).date().isoformat(),
            "validation_start": test_start.date().isoformat(),
            "validation_end": test_end.date().isoformat(),
            "validation_last_label_maturity": validation_last_maturity.date().isoformat(),
            "train_factor_mean_ic": train_evidence,
            "dynamic_weights": dynamic_weights,
        }
        for contender in CONTENDERS:
            record[contender] = _summarize_rows(rows_by_contender[contender])
        fold_records.append(record)
        previous_validation_label_maturity = validation_last_maturity

    evaluated = [fold for fold in fold_records if fold.get("status") == "EVALUATED"]
    return {
        "all_fold_records": fold_records,
        "evaluated_fold_count": len(evaluated),
        "no_signal_fold_count": sum(
            1 for fold in fold_records if fold.get("status") != "EVALUATED"
        ),
        "aggregates": {
            contender: _aggregate_folds(evaluated, contender)
            for contender in CONTENDERS
        },
        "paired_dynamic_vs_ew5": _paired(evaluated, DYNAMIC, EW5),
        "paired_dynamic_vs_champion": _paired(evaluated, DYNAMIC, CHAMPION),
        "paired_ew5_vs_champion": _paired(evaluated, EW5, CHAMPION),
    }


def main() -> int:
    panel, calendar = ew.build_common_panel()
    results = {
        str(horizon): run_horizon(panel, calendar, horizon)
        for horizon in HORIZONS
    }

    receipt = {
        "contract": "LONG_ONLY_COST_SENSITIVITY_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "contenders": CONTENDERS,
        "champion_reference": CHAMPION,
        "factor_universe": ew.FACTORS,
        "common_panel_rows": int(len(panel)),
        "common_signal_dates": int(panel["signal_date"].nunique()),
        "selection": "TOP_20_PERCENT_EQUAL_WEIGHT",
        "fold_boundary_policy": "RESET_TO_CASH",
        "turnover_definition": "SUM_ABS_NEW_MINUS_OLD_WEIGHT",
        "cost_scenarios_bps_per_unit_traded_notional": COST_BPS,
        "cost_scenarios_are_observed_historical_costs": False,
        "results": results,
        "limitations": [
            "This is a long-leg forward-return cost-sensitivity diagnostic, not a self-financing NAV backtest.",
            "Forward labels overlap at longer horizons while signal dates are monthly.",
            "Cost bps are transparent sensitivity scenarios, not observed historical bid-ask/slippage/market-impact data.",
            "Capacity is not claimed because authoritative historical execution microstructure is not integrated.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK.",
            "No automatic champion or production promotion is authorized."
        ],
    }

    out = Path(
        "research/evidence_runs/"
        "long_only_cost_sensitivity_v1.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
