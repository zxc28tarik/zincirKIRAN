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
import run_real_walk_forward_factor_stability as wf  # noqa: E402

FACTORS = ew.FACTORS
CHAMPION = ew.CHAMPION
EW5 = ew.COMPOSITE
DYNAMIC = "TRAIN_ONLY_EVIDENCE_WEIGHTED_5F"
HORIZONS = ew.HORIZONS


def _monthly_ic(
    panel: pd.DataFrame,
    score: pd.Series,
    horizon: int,
    allowed_dates: list[pd.Timestamp],
) -> pd.DataFrame:
    target = f"TARGET_{horizon}"
    work = panel[["signal_date", "ticker", target]].copy()
    work["score"] = score
    work = work.loc[work["signal_date"].isin(allowed_dates)].dropna()
    rows: list[dict[str, object]] = []
    for signal, group in work.groupby("signal_date"):
        if len(group) < 20:
            continue
        ic = group["score"].astype(float).rank().corr(
            group[target].astype(float).rank()
        )
        if pd.isna(ic):
            continue
        spread = None
        ranks = group["score"].astype(float).rank(method="first")
        try:
            q = pd.qcut(ranks, 5, labels=False) + 1
            qmeans = group[target].astype(float).groupby(q).mean()
            if 1 in qmeans.index and 5 in qmeans.index:
                spread = float(qmeans.loc[5] - qmeans.loc[1])
        except ValueError:
            pass
        rows.append(
            {
                "signal_date": pd.Timestamp(signal),
                "ic": float(ic),
                "spread": spread,
                "n": int(len(group)),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["signal_date", "ic", "spread", "n"])
    return pd.DataFrame(rows).sort_values("signal_date").reset_index(drop=True)


def _factor_train_evidence(
    panel: pd.DataFrame,
    horizon: int,
    train_dates: list[pd.Timestamp],
) -> dict[str, float | None]:
    evidence: dict[str, float | None] = {}
    for factor in FACTORS:
        rows = _monthly_ic(panel, panel[factor], horizon, train_dates)
        evidence[factor] = (
            None if rows.empty else float(rows["ic"].astype(float).mean())
        )
    return evidence


def _weights(evidence: dict[str, float | None]) -> dict[str, float] | None:
    positive = {
        factor: max(float(value), 0.0)
        for factor, value in evidence.items()
        if value is not None and np.isfinite(value)
    }
    denominator = sum(positive.values())
    if denominator <= 0:
        return None
    return {
        factor: positive.get(factor, 0.0) / denominator
        for factor in FACTORS
    }


def _score(panel: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    return sum(
        panel[factor].astype(float) * weights[factor]
        for factor in FACTORS
    )


def _fold_summary(rows: pd.DataFrame) -> dict[str, object]:
    return wf.summarize_months(rows)


def _aggregate(folds: list[dict[str, object]], key: str) -> dict[str, object]:
    vals = [
        float(fold[key]["mean_ic"])
        for fold in folds
        if fold[key]["mean_ic"] is not None
    ]
    if not vals:
        return {
            "folds": 0,
            "mean_test_ic": None,
            "worst_fold_ic": None,
            "positive_fold_share": None,
            "stability": "UNAVAILABLE",
        }
    mean_ic = float(np.mean(vals))
    return {
        "folds": len(vals),
        "mean_test_ic": mean_ic,
        "worst_fold_ic": min(vals),
        "positive_fold_share": sum(v > 0 for v in vals) / len(vals),
        "stability": wf.classify_stability(vals, mean_ic=mean_ic),
    }


def _paired(folds: list[dict[str, object]], left: str, right: str) -> dict[str, object]:
    diffs: list[float] = []
    for fold in folds:
        left_ic = fold[left]["mean_ic"]
        right_ic = fold[right]["mean_ic"]
        if left_ic is None or right_ic is None:
            continue
        diffs.append(float(left_ic - right_ic))
    return {
        "paired_folds": len(diffs),
        "mean_ic_difference": None if not diffs else float(np.mean(diffs)),
        "median_ic_difference": None if not diffs else float(np.median(diffs)),
        "left_beats_right_fold_share": (
            None if not diffs else sum(v > 0 for v in diffs) / len(diffs)
        ),
    }


def run_horizon(
    panel: pd.DataFrame,
    calendar: pd.DataFrame,
    horizon: int,
) -> dict[str, object]:
    signal_dates = sorted(
        pd.Timestamp(x) for x in panel["signal_date"].dropna().unique()
    )
    maturity = wf.maturity_map(signal_dates, calendar, horizon)
    blocks = wf.validation_blocks(signal_dates, maturity)

    folds: list[dict[str, object]] = []
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

        evidence = _factor_train_evidence(panel, horizon, train_dates)
        weights = _weights(evidence)
        if weights is None:
            folds.append(
                {
                    "fold_id": f"H{horizon}-F{idx}",
                    "validation_start": test_start.date().isoformat(),
                    "validation_end": test_end.date().isoformat(),
                    "status": "NO_SIGNAL_ZERO_POSITIVE_TRAIN_EVIDENCE",
                    "train_factor_mean_ic": evidence,
                    "weights": None,
                }
            )
            previous_validation_label_maturity = validation_last_maturity
            continue

        dynamic_score = _score(panel, weights)
        ew5_score = panel[EW5]
        champion_score = panel[CHAMPION]

        dynamic_rows = _monthly_ic(panel, dynamic_score, horizon, test_dates)
        ew5_rows = _monthly_ic(panel, ew5_score, horizon, test_dates)
        champion_rows = _monthly_ic(panel, champion_score, horizon, test_dates)

        if len(dynamic_rows) < wf.MIN_TEST_MONTHS:
            previous_validation_label_maturity = validation_last_maturity
            continue

        folds.append(
            {
                "fold_id": f"H{horizon}-F{idx}",
                "status": "EVALUATED",
                "train_start": min(train_dates).date().isoformat(),
                "train_end": max(train_dates).date().isoformat(),
                "train_last_label_maturity": max(
                    maturity[signal]
                    for signal in train_dates
                    if maturity[signal] is not None
                ).date().isoformat(),
                "validation_start": test_start.date().isoformat(),
                "validation_end": test_end.date().isoformat(),
                "validation_last_label_maturity": validation_last_maturity.date().isoformat(),
                "train_factor_mean_ic": evidence,
                "weights": weights,
                DYNAMIC: _fold_summary(dynamic_rows),
                EW5: _fold_summary(ew5_rows),
                CHAMPION: _fold_summary(champion_rows),
            }
        )
        previous_validation_label_maturity = validation_last_maturity

    evaluated = [fold for fold in folds if fold.get("status") == "EVALUATED"]
    return {
        "all_fold_records": folds,
        "evaluated_fold_count": len(evaluated),
        "no_signal_fold_count": sum(
            1 for fold in folds if fold.get("status") != "EVALUATED"
        ),
        DYNAMIC: _aggregate(evaluated, DYNAMIC),
        EW5: _aggregate(evaluated, EW5),
        CHAMPION: _aggregate(evaluated, CHAMPION),
        "paired_dynamic_vs_ew5": _paired(evaluated, DYNAMIC, EW5),
        "paired_dynamic_vs_champion": _paired(evaluated, DYNAMIC, CHAMPION),
    }


def main() -> int:
    panel, calendar = ew.build_common_panel()
    results = {
        str(horizon): run_horizon(panel, calendar, horizon)
        for horizon in HORIZONS
    }

    receipt = {
        "contract": "NESTED_TRAIN_ONLY_EVIDENCE_WEIGHTED_COMPOSITE_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "factor_universe": FACTORS,
        "common_panel_rows": int(len(panel)),
        "common_signal_dates": int(panel["signal_date"].nunique()),
        "weight_rule": "MAX_TRAIN_MEAN_IC_ZERO_THEN_NORMALIZE",
        "validation_data_used_in_weights": False,
        "missingness": "REQUIRE_ALL_5_FACTORS_NO_NEUTRAL_FILL",
        "benchmarks": [EW5, CHAMPION],
        "results": results,
        "limitations": [
            "Weights are adaptive but use only matured training evidence.",
            "The same five-factor universe was selected from earlier research, so this is not a virgin external holdout.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK.",
            "Forward returns remain the adjusted-close-minus-XU100 diagnostic proxy.",
            "No automatic champion or production promotion is authorized."
        ]
    }

    out = Path(
        "research/evidence_runs/"
        "nested_train_only_evidence_weighted_composite_v1.json"
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
