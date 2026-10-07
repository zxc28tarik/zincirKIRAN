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
import run_nested_train_only_evidence_weighted_composite as dyn  # noqa: E402
import run_real_walk_forward_factor_stability as wf  # noqa: E402

FEATURES = ew.FACTORS
CHAMPION = ew.CHAMPION
EW5 = ew.COMPOSITE
DYNAMIC = dyn.DYNAMIC
RIDGE = "FIXED_RIDGE_5F"
CONTENDERS = (CHAMPION, EW5, DYNAMIC, RIDGE)
HORIZONS = ew.HORIZONS
RIDGE_PENALTY = 1.0


def fit_ridge(
    train: pd.DataFrame,
    target_col: str,
) -> dict[str, object]:
    usable = train[list(FEATURES) + [target_col]].dropna().copy()
    if usable.empty:
        raise RuntimeError("ridge training sample is empty")

    x = usable[list(FEATURES)].astype(float).to_numpy()
    y = usable[target_col].astype(float).to_numpy()

    means = x.mean(axis=0)
    scales = x.std(axis=0, ddof=0)
    scales = np.where(scales > 0, scales, 1.0)
    z = (x - means) / scales

    design = np.column_stack([np.ones(len(z)), z])
    gram = design.T @ design
    penalty = np.diag([0.0] + [RIDGE_PENALTY] * len(FEATURES))
    rhs = design.T @ y
    solution = np.linalg.solve(gram + penalty, rhs)

    return {
        "training_observations": int(len(usable)),
        "means": means,
        "scales": scales,
        "intercept": float(solution[0]),
        "coefficients": solution[1:],
    }


def score_ridge(
    panel: pd.DataFrame,
    model: dict[str, object],
) -> pd.Series:
    x = panel[list(FEATURES)].astype(float).to_numpy()
    means = np.asarray(model["means"], dtype=float)
    scales = np.asarray(model["scales"], dtype=float)
    coefficients = np.asarray(model["coefficients"], dtype=float)
    z = (x - means) / scales
    score = float(model["intercept"]) + z @ coefficients
    return pd.Series(score, index=panel.index, dtype=float)


def dated_metrics(
    panel: pd.DataFrame,
    score: pd.Series,
    horizon: int,
    dates: list[pd.Timestamp],
) -> pd.DataFrame:
    target = f"TARGET_{horizon}"
    work = panel[["signal_date", "ticker", target]].copy()
    work["score"] = score
    work = work.loc[work["signal_date"].isin(dates)].dropna()

    rows: list[dict[str, object]] = []
    for signal, group in work.groupby("signal_date"):
        if len(group) < 20:
            continue
        x = group["score"].astype(float)
        y = group[target].astype(float)
        ic = x.rank().corr(y.rank())
        if pd.isna(ic):
            continue

        top = None
        spread = None
        ranks = x.rank(method="first")
        try:
            q = pd.qcut(ranks, 5, labels=False) + 1
            qmeans = y.groupby(q).mean()
            if 5 in qmeans.index:
                top = float(qmeans.loc[5])
            if 1 in qmeans.index and 5 in qmeans.index:
                spread = float(qmeans.loc[5] - qmeans.loc[1])
        except ValueError:
            pass

        rows.append(
            {
                "signal_date": pd.Timestamp(signal),
                "ic": float(ic),
                "top": top,
                "spread": spread,
                "n": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def summarize(rows: pd.DataFrame) -> dict[str, object]:
    if rows.empty:
        return {
            "months": 0,
            "mean_ic": None,
            "positive_ic_share": None,
            "mean_top_quintile_forward_excess_proxy": None,
            "mean_q5_minus_q1": None,
        }
    ic = rows["ic"].astype(float).to_numpy()
    tops = rows["top"].dropna().astype(float).to_numpy()
    spreads = rows["spread"].dropna().astype(float).to_numpy()
    return {
        "months": int(len(rows)),
        "mean_ic": float(np.mean(ic)),
        "positive_ic_share": float(np.mean(ic > 0)),
        "mean_top_quintile_forward_excess_proxy": (
            None if len(tops) == 0 else float(np.mean(tops))
        ),
        "mean_q5_minus_q1": (
            None if len(spreads) == 0 else float(np.mean(spreads))
        ),
    }


def aggregate(folds: list[dict[str, object]], contender: str) -> dict[str, object]:
    vals = [
        fold[contender]
        for fold in folds
        if fold.get("status") == "EVALUATED"
        and contender in fold
        and fold[contender]["mean_ic"] is not None  # type: ignore[index]
    ]
    if not vals:
        return {
            "folds": 0,
            "mean_test_ic": None,
            "worst_fold_ic": None,
            "positive_fold_share": None,
            "stability": "UNAVAILABLE",
            "mean_top_quintile_forward_excess_proxy": None,
            "mean_q5_minus_q1": None,
        }

    ics = [float(item["mean_ic"]) for item in vals]  # type: ignore[index]
    tops = [
        float(item["mean_top_quintile_forward_excess_proxy"])  # type: ignore[index]
        for item in vals
        if item["mean_top_quintile_forward_excess_proxy"] is not None  # type: ignore[index]
    ]
    spreads = [
        float(item["mean_q5_minus_q1"])  # type: ignore[index]
        for item in vals
        if item["mean_q5_minus_q1"] is not None  # type: ignore[index]
    ]
    mean_ic = float(np.mean(ics))
    return {
        "folds": int(len(ics)),
        "mean_test_ic": mean_ic,
        "worst_fold_ic": float(min(ics)),
        "positive_fold_share": float(np.mean(np.asarray(ics) > 0)),
        "stability": wf.classify_stability(ics, mean_ic=mean_ic),
        "mean_top_quintile_forward_excess_proxy": (
            None if not tops else float(np.mean(tops))
        ),
        "mean_q5_minus_q1": (
            None if not spreads else float(np.mean(spreads))
        ),
    }


def paired(
    folds: list[dict[str, object]],
    left: str,
    right: str,
) -> dict[str, object]:
    ic_diffs: list[float] = []
    top_diffs: list[float] = []
    for fold in folds:
        if fold.get("status") != "EVALUATED":
            continue
        if left not in fold or right not in fold:
            continue
        li = fold[left]["mean_ic"]  # type: ignore[index]
        ri = fold[right]["mean_ic"]  # type: ignore[index]
        if li is not None and ri is not None:
            ic_diffs.append(float(li) - float(ri))
        lt = fold[left]["mean_top_quintile_forward_excess_proxy"]  # type: ignore[index]
        rt = fold[right]["mean_top_quintile_forward_excess_proxy"]  # type: ignore[index]
        if lt is not None and rt is not None:
            top_diffs.append(float(lt) - float(rt))
    return {
        "paired_folds_ic": int(len(ic_diffs)),
        "mean_ic_difference": (
            None if not ic_diffs else float(np.mean(ic_diffs))
        ),
        "left_beats_right_ic_fold_share": (
            None if not ic_diffs else float(np.mean(np.asarray(ic_diffs) > 0))
        ),
        "paired_folds_long_leg": int(len(top_diffs)),
        "mean_top_quintile_difference": (
            None if not top_diffs else float(np.mean(top_diffs))
        ),
        "left_beats_right_long_leg_fold_share": (
            None if not top_diffs else float(np.mean(np.asarray(top_diffs) > 0))
        ),
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

    records: list[dict[str, object]] = []
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
        model = fit_ridge(train, target)
        ridge_score = score_ridge(panel, model)

        evidence = dyn._factor_train_evidence(panel, horizon, train_dates)
        dynamic_weights = dyn._weights(evidence)
        if dynamic_weights is None:
            records.append(
                {
                    "fold_id": f"H{horizon}-F{idx}",
                    "status": "NO_SIGNAL_DYNAMIC_ZERO_POSITIVE_EVIDENCE",
                    "validation_start": test_start.date().isoformat(),
                    "validation_end": test_end.date().isoformat(),
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

        record: dict[str, object] = {
            "fold_id": f"H{horizon}-F{idx}",
            "status": "EVALUATED",
            "train_start": min(train_dates).date().isoformat(),
            "train_end": max(train_dates).date().isoformat(),
            "validation_start": test_start.date().isoformat(),
            "validation_end": test_end.date().isoformat(),
            "validation_last_label_maturity": validation_last_maturity.date().isoformat(),
            "ridge_training_observations": model["training_observations"],
            "ridge_intercept": model["intercept"],
            "ridge_coefficients": {
                feature: float(value)
                for feature, value in zip(
                    FEATURES,
                    np.asarray(model["coefficients"], dtype=float),
                    strict=True,
                )
            },
            "dynamic_weights": dynamic_weights,
        }
        for contender, score in scores.items():
            record[contender] = summarize(
                dated_metrics(panel, score, horizon, test_dates)
            )
        records.append(record)
        previous_validation_label_maturity = validation_last_maturity

    evaluated = [row for row in records if row.get("status") == "EVALUATED"]
    return {
        "all_fold_records": records,
        "evaluated_fold_count": int(len(evaluated)),
        "aggregates": {
            contender: aggregate(evaluated, contender)
            for contender in CONTENDERS
        },
        "paired_ridge_vs_champion": paired(evaluated, RIDGE, CHAMPION),
        "paired_ridge_vs_ew5": paired(evaluated, RIDGE, EW5),
        "paired_ridge_vs_dynamic": paired(evaluated, RIDGE, DYNAMIC),
    }


def main() -> int:
    panel, calendar = ew.build_common_panel()
    results = {
        str(horizon): run_horizon(panel, calendar, horizon)
        for horizon in HORIZONS
    }

    receipt = {
        "contract": "REAL_FIXED_RIDGE_ML_5F_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "model": "DETERMINISTIC_LINEAR_RIDGE",
        "ridge_penalty": RIDGE_PENALTY,
        "hyperparameter_search": False,
        "features": FEATURES,
        "common_panel_rows": int(len(panel)),
        "common_signal_dates": int(panel["signal_date"].nunique()),
        "comparators": (CHAMPION, EW5, DYNAMIC),
        "training_protocol": {
            "train_rows_only_standardization": True,
            "matured_labels_only": True,
            "validation_information_in_fit": False,
            "pooled_stock_month_fit": True,
            "target_winsorization": False,
            "feature_removal_after_results": False,
        },
        "results": results,
        "limitations": [
            "This is a fixed ridge baseline; lambda=1.0 was not optimized.",
            "The feature universe was selected by earlier research and is not a virgin external holdout.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK.",
            "Forward returns remain adjusted-close-minus-XU100 diagnostic proxies.",
            "No automatic champion or production promotion is authorized."
        ],
    }

    out = Path("research/evidence_runs/real_fixed_ridge_ml_5f_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
