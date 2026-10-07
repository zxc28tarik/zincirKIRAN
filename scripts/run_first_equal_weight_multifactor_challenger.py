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

import run_real_sector_neutral_decorrelation as sn  # noqa: E402
import run_real_walk_forward_factor_stability as wf  # noqa: E402

FACTORS = (
    "HIGH_52W_PROXIMITY",
    "LOW_VOL_63D",
    "MOM_6_1",
    "operating_margin_acceleration",
    "gross_margin_acceleration",
)
WEIGHTS = {factor: 0.20 for factor in FACTORS}
CHAMPION = "HIGH_52W_PROXIMITY"
COMPOSITE = "EW5_COMPOSITE"
HORIZONS = (20, 60, 120, 252)


def build_common_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    frames, calendar = wf.build_panels()

    base = frames[CHAMPION][
        ["signal_date", "ticker", "sector_neutral_score"]
        + [f"TARGET_{h}" for h in HORIZONS]
    ].copy()
    base = base.rename(columns={"sector_neutral_score": CHAMPION})

    for factor in FACTORS[1:]:
        part = frames[factor][
            ["signal_date", "ticker", "sector_neutral_score"]
        ].copy()
        part = part.rename(columns={"sector_neutral_score": factor})
        base = base.merge(
            part,
            on=["signal_date", "ticker"],
            how="inner",
            validate="one_to_one",
        )

    common = base.dropna(subset=list(FACTORS)).copy()
    common[COMPOSITE] = sum(
        common[factor].astype(float) * WEIGHTS[factor]
        for factor in FACTORS
    )
    return common.sort_values(["signal_date", "ticker"]).reset_index(drop=True), calendar


def paired_comparison(
    composite: dict[str, object],
    champion: dict[str, object],
) -> dict[str, object]:
    cfolds = {
        fold["validation_start"]: fold
        for fold in composite.get("folds", [])
    }
    hfolds = {
        fold["validation_start"]: fold
        for fold in champion.get("folds", [])
    }
    common_keys = sorted(set(cfolds) & set(hfolds))
    diffs: list[float] = []
    rows: list[dict[str, object]] = []
    beats = 0

    for key in common_keys:
        c_ic = cfolds[key]["test"]["mean_ic"]
        h_ic = hfolds[key]["test"]["mean_ic"]
        if c_ic is None or h_ic is None:
            continue
        diff = float(c_ic - h_ic)
        diffs.append(diff)
        beats += int(diff > 0)
        rows.append(
            {
                "validation_start": key,
                "composite_mean_ic": float(c_ic),
                "champion_mean_ic": float(h_ic),
                "difference": diff,
            }
        )

    return {
        "paired_folds": len(diffs),
        "mean_ic_difference_vs_champion": (
            float(np.mean(diffs)) if diffs else None
        ),
        "median_ic_difference_vs_champion": (
            float(np.median(diffs)) if diffs else None
        ),
        "fraction_folds_composite_beats_champion": (
            beats / len(diffs) if diffs else None
        ),
        "fold_differences": rows,
    }


def run_score(
    panel: pd.DataFrame,
    calendar: pd.DataFrame,
    score_col: str,
    horizon: int,
) -> dict[str, object]:
    frame = panel[
        ["signal_date", "ticker", score_col]
        + [f"TARGET_{h}" for h in HORIZONS]
    ].copy()
    frame = frame.rename(columns={score_col: "sector_neutral_score"})
    return wf.run_factor_horizon(
        frame,
        calendar,
        score_col,
        horizon,
        "sector_neutral_score",
    )


def main() -> int:
    panel, calendar = build_common_panel()

    results: dict[str, object] = {}
    for horizon in HORIZONS:
        contenders: dict[str, object] = {}
        for contender in (COMPOSITE,) + FACTORS:
            contenders[contender] = run_score(
                panel,
                calendar,
                contender,
                horizon,
            )

        results[str(horizon)] = {
            "common_sample_rows": int(
                panel[
                    ["signal_date", "ticker", COMPOSITE, f"TARGET_{horizon}"]
                ].dropna().shape[0]
            ),
            "common_signal_dates": int(
                panel.loc[
                    panel[f"TARGET_{horizon}"].notna(),
                    "signal_date",
                ].nunique()
            ),
            "contenders": contenders,
            "paired_composite_vs_champion": paired_comparison(
                contenders[COMPOSITE],
                contenders[CHAMPION],
            ),
        }

    receipt = {
        "contract": "FIRST_EQUAL_WEIGHT_MULTIFACTOR_CHALLENGER_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "champion": CHAMPION,
        "challenger": COMPOSITE,
        "factors": FACTORS,
        "weights": WEIGHTS,
        "weight_selection": "PREREGISTERED_EQUAL_WEIGHT_NO_OPTIMIZATION",
        "missingness": "REQUIRE_ALL_5_FACTORS_NO_NEUTRAL_FILL",
        "comparison_sample": "EXACT_COMMON_5_OF_5_ROWS",
        "walk_forward_protocol": {
            "source": "IMPLEMENTATION_35",
            "chronological_only": True,
            "expanding_train": True,
            "train_label_maturity_purge": True,
            "validation_label_maturity_embargo": True,
            "test_block_months": wf.TEST_BLOCK_MONTHS,
            "minimum_folds_for_stability_classification": 2,
        },
        "common_panel": {
            "rows": int(len(panel)),
            "signal_dates": int(panel["signal_date"].nunique()),
        },
        "results": results,
        "limitations": [
            "The composite weights are fixed equal weights and are not trained.",
            "Financial inputs retain EXPERIMENTAL_VERSION_RISK.",
            "Forward returns remain the adjusted-close-minus-XU100 diagnostic proxy.",
            "H252 may remain insufficient for stability classification after true label embargo.",
            "This run cannot automatically replace the benchmark champion.",
        ],
    }

    out = Path(
        "research/evidence_runs/"
        "first_equal_weight_multifactor_challenger_v1.json"
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
