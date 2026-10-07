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

import run_first_equal_weight_multifactor_challenger as ew  # noqa: E402
import run_historical_liquidity_capacity as cap  # noqa: E402
import run_long_only_cost_sensitivity as cost  # noqa: E402
import run_nested_train_only_evidence_weighted_composite as dyn  # noqa: E402
import run_real_fixed_ridge_ml_challenger as ml  # noqa: E402
import run_real_walk_forward_factor_stability as wf  # noqa: E402

CHAMPION = ew.CHAMPION
EW5 = ew.COMPOSITE
DYNAMIC = dyn.DYNAMIC
RIDGE = ml.RIDGE
CONTENDERS = (CHAMPION, EW5, DYNAMIC, RIDGE)
HORIZONS = ew.HORIZONS


def summarize_fold_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "cost": cost._summarize_rows(rows),
        "capacity": cap._summarize_capacity(rows),
    }


def aggregate_contender(
    folds: list[dict[str, object]],
    contender: str,
) -> dict[str, object]:
    summaries = [
        fold[contender]
        for fold in folds
        if fold.get("status") == "EVALUATED" and contender in fold
    ]
    if not summaries:
        return {"folds": 0}

    gross = [
        float(item["cost"]["mean_gross_forward_excess_proxy"])  # type: ignore[index]
        for item in summaries
    ]
    turnover = [
        float(item["cost"]["mean_gross_turnover"])  # type: ignore[index]
        for item in summaries
    ]

    cost_scenarios: dict[str, object] = {}
    for bps in cost.COST_BPS:
        key = f"{int(bps)}bps"
        vals = [
            float(
                item["cost"]["cost_scenarios"][key]["mean_net_forward_excess_proxy"]  # type: ignore[index]
            )
            for item in summaries
        ]
        cost_scenarios[key] = {
            "mean_fold_net_forward_excess_proxy": float(np.mean(vals)),
            "worst_fold_net_forward_excess_proxy": float(np.min(vals)),
            "positive_fold_share": float(np.mean(np.asarray(vals) > 0)),
        }

    capacity_scenarios: dict[str, object] = {}
    for participation in cap.PARTICIPATION_RATES:
        for days in cap.EXECUTION_DAYS:
            key = cap._scenario_key(participation, days)
            medians = [
                float(item["capacity"]["scenarios"][key]["median_capacity_try"])  # type: ignore[index]
                for item in summaries
                if item["capacity"]["scenarios"][key]["median_capacity_try"] is not None  # type: ignore[index]
            ]
            worsts = [
                float(item["capacity"]["scenarios"][key]["worst_capacity_try"])  # type: ignore[index]
                for item in summaries
                if item["capacity"]["scenarios"][key]["worst_capacity_try"] is not None  # type: ignore[index]
            ]
            support: dict[str, float | None] = {}
            for notional in cap.NOTIONALS_TRY:
                vals = [
                    float(
                        item["capacity"]["scenarios"][key][
                            "support_fraction_by_portfolio_notional_try"
                        ][str(notional)]  # type: ignore[index]
                    )
                    for item in summaries
                ]
                support[str(notional)] = (
                    None if not vals else float(np.mean(vals))
                )
            capacity_scenarios[key] = {
                "mean_fold_median_capacity_try": (
                    None if not medians else float(np.mean(medians))
                ),
                "worst_capacity_across_folds_try": (
                    None if not worsts else float(np.min(worsts))
                ),
                "mean_fold_support_fraction_by_portfolio_notional_try": support,
            }

    return {
        "folds": int(len(summaries)),
        "mean_fold_gross_forward_excess_proxy": float(np.mean(gross)),
        "worst_fold_gross_forward_excess_proxy": float(np.min(gross)),
        "positive_gross_fold_share": float(np.mean(np.asarray(gross) > 0)),
        "mean_fold_gross_turnover": float(np.mean(turnover)),
        "total_missing_adv_dates": int(
            sum(int(item["capacity"]["missing_adv_dates"]) for item in summaries)  # type: ignore[index]
        ),
        "mean_fold_selected_adv_coverage": float(
            np.mean(
                [
                    float(
                        item["capacity"]["selected_adv"]["mean_selected_adv_coverage"]  # type: ignore[index]
                    )
                    for item in summaries
                ]
            )
        ),
        "cost_scenarios": cost_scenarios,
        "capacity_scenarios": capacity_scenarios,
    }


def paired_ridge(
    folds: list[dict[str, object]],
    other: str,
) -> dict[str, object]:
    gross: list[float] = []
    turnover: list[float] = []
    cost_diffs: dict[str, list[float]] = {
        f"{int(bps)}bps": [] for bps in cost.COST_BPS
    }
    capacity_diffs: dict[str, list[float]] = {
        cap._scenario_key(p, d): []
        for p in cap.PARTICIPATION_RATES
        for d in cap.EXECUTION_DAYS
    }

    for fold in folds:
        if fold.get("status") != "EVALUATED":
            continue
        if RIDGE not in fold or other not in fold:
            continue
        left = fold[RIDGE]
        right = fold[other]
        gross.append(
            float(left["cost"]["mean_gross_forward_excess_proxy"])  # type: ignore[index]
            - float(right["cost"]["mean_gross_forward_excess_proxy"])  # type: ignore[index]
        )
        turnover.append(
            float(left["cost"]["mean_gross_turnover"])  # type: ignore[index]
            - float(right["cost"]["mean_gross_turnover"])  # type: ignore[index]
        )
        for key in cost_diffs:
            cost_diffs[key].append(
                float(
                    left["cost"]["cost_scenarios"][key]["mean_net_forward_excess_proxy"]  # type: ignore[index]
                )
                - float(
                    right["cost"]["cost_scenarios"][key]["mean_net_forward_excess_proxy"]  # type: ignore[index]
                )
            )
        for key in capacity_diffs:
            lm = left["capacity"]["scenarios"][key]["median_capacity_try"]  # type: ignore[index]
            rm = right["capacity"]["scenarios"][key]["median_capacity_try"]  # type: ignore[index]
            if lm is not None and rm is not None:
                capacity_diffs[key].append(float(lm) - float(rm))

    return {
        "paired_folds": int(len(gross)),
        "mean_gross_forward_excess_difference": (
            None if not gross else float(np.mean(gross))
        ),
        "ridge_beats_other_gross_fold_share": (
            None if not gross else float(np.mean(np.asarray(gross) > 0))
        ),
        "mean_turnover_difference": (
            None if not turnover else float(np.mean(turnover))
        ),
        "cost_scenarios": {
            key: {
                "mean_net_difference": (
                    None if not vals else float(np.mean(vals))
                ),
                "ridge_beats_other_fold_share": (
                    None if not vals else float(np.mean(np.asarray(vals) > 0))
                ),
            }
            for key, vals in cost_diffs.items()
        },
        "capacity_scenarios": {
            key: {
                "mean_median_capacity_difference_try": (
                    None if not vals else float(np.mean(vals))
                )
            }
            for key, vals in capacity_diffs.items()
        },
    }


def run_horizon(
    panel: pd.DataFrame,
    calendar: pd.DataFrame,
    adv_map: dict[tuple[pd.Timestamp, str], float],
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

        train = panel.loc[panel["signal_date"].isin(train_dates)].copy()
        ridge_model = ml.fit_ridge(train, target)
        ridge_score = ml.score_ridge(panel, ridge_model)

        train_evidence = dyn._factor_train_evidence(panel, horizon, train_dates)
        dynamic_weights = dyn._weights(train_evidence)
        if dynamic_weights is None:
            fold_records.append(
                {
                    "fold_id": f"H{horizon}-F{idx}",
                    "status": "NO_SIGNAL_DYNAMIC_ZERO_POSITIVE_EVIDENCE",
                }
            )
            previous_validation_label_maturity = validation_last_maturity
            continue

        scores = {
            CHAMPION: panel[CHAMPION].astype(float),
            EW5: panel[EW5].astype(float),
            DYNAMIC: dyn._score(panel, dynamic_weights),
            RIDGE: ridge_score,
        }

        previous_weights: dict[str, dict[str, float]] = {
            contender: {} for contender in CONTENDERS
        }
        rows: dict[str, list[dict[str, object]]] = {
            contender: [] for contender in CONTENDERS
        }

        for signal_date in test_dates:
            group = panel.loc[panel["signal_date"] == signal_date]
            for contender in CONTENDERS:
                previous = previous_weights[contender]
                built = cost._portfolio_row(
                    group,
                    scores[contender].loc[group.index],
                    target,
                    previous,
                )
                if built is None:
                    continue
                cost_row, current = built
                capacity_row = cap._capacity_row(
                    signal_date=signal_date,
                    previous=previous,
                    current=current,
                    adv_map=adv_map,
                )
                combined = dict(capacity_row)
                combined.update(cost_row)
                combined["signal_date"] = signal_date.date().isoformat()
                rows[contender].append(combined)
                previous_weights[contender] = current

        if any(len(rows[c]) < wf.MIN_TEST_MONTHS for c in CONTENDERS):
            previous_validation_label_maturity = validation_last_maturity
            continue

        record: dict[str, object] = {
            "fold_id": f"H{horizon}-F{idx}",
            "status": "EVALUATED",
            "validation_start": test_start.date().isoformat(),
            "validation_end": test_end.date().isoformat(),
            "ridge_training_observations": ridge_model["training_observations"],
            "ridge_coefficients": {
                feature: float(value)
                for feature, value in zip(
                    ml.FEATURES,
                    np.asarray(ridge_model["coefficients"], dtype=float),
                    strict=True,
                )
            },
            "dynamic_weights": dynamic_weights,
        }
        for contender in CONTENDERS:
            record[contender] = summarize_fold_rows(rows[contender])
        fold_records.append(record)
        previous_validation_label_maturity = validation_last_maturity

    evaluated = [row for row in fold_records if row.get("status") == "EVALUATED"]
    return {
        "all_fold_records": fold_records,
        "evaluated_fold_count": int(len(evaluated)),
        "aggregates": {
            contender: aggregate_contender(evaluated, contender)
            for contender in CONTENDERS
        },
        "paired_ridge_vs_champion": paired_ridge(evaluated, CHAMPION),
        "paired_ridge_vs_ew5": paired_ridge(evaluated, EW5),
        "paired_ridge_vs_dynamic": paired_ridge(evaluated, DYNAMIC),
    }


def main() -> int:
    panel, calendar = ew.build_common_panel()
    adv_map, adv_source = cap.load_adv63()
    results = {
        str(horizon): run_horizon(panel, calendar, adv_map, horizon)
        for horizon in HORIZONS
    }

    receipt = {
        "contract": "ML_PORTFOLIO_COST_CAPACITY_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "contenders": CONTENDERS,
        "ridge_penalty": ml.RIDGE_PENALTY,
        "ridge_hyperparameter_search": False,
        "common_panel_rows": int(len(panel)),
        "common_signal_dates": int(panel["signal_date"].nunique()),
        "cost_scenarios_bps": cost.COST_BPS,
        "historical_adv_source": adv_source,
        "participation_rates": cap.PARTICIPATION_RATES,
        "execution_days": cap.EXECUTION_DAYS,
        "illustrative_portfolio_notionals_try": cap.NOTIONALS_TRY,
        "results": results,
        "limitations": [
            "This is a forward-return portfolio diagnostic, not a self-financing overlapping-horizon NAV backtest.",
            "Cost bps remain sensitivity scenarios rather than observed historical execution costs.",
            "ADV capacity uses validated derived daily volume, not official Borsa daily volume.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK.",
            "No hyperparameter, portfolio-size, liquidity-threshold, champion, or production optimization is authorized."
        ],
    }

    out = Path("research/evidence_runs/ml_portfolio_cost_capacity_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
