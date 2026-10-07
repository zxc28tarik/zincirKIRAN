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

import run_real_sector_neutral_decorrelation as sn  # noqa: E402

HORIZONS = (20, 60, 120, 252)
FACTOR_SET = (
    "roa",
    "operating_profitability",
    "gross_profitability",
    "operating_margin",
    "gross_margin",
    "operating_margin_acceleration",
    "gross_margin_acceleration",
    "asset_growth",
    "HIGH_52W_PROXIMITY",
    "LOW_VOL_63D",
    "MOM_6_1",
)

TRANSFORMS = (
    "RAW_DIRECTION_NORMALIZED",
    "WINSOR_1_99",
    "WINSOR_2_5_97_5",
    "CROSS_SECTION_ZSCORE_WINSOR_1_99",
    "SECTOR_NEUTRAL_PERCENTILE",
)


def winsorize_by_date(series: pd.Series, dates: pd.Series, lower: float, upper: float) -> pd.Series:
    out = pd.Series(np.nan, index=series.index, dtype=float)
    work = pd.DataFrame({"date": dates, "value": series})
    for _, group in work.groupby("date"):
        values = group["value"].dropna()
        if len(values) < 20:
            continue
        lo = float(values.quantile(lower))
        hi = float(values.quantile(upper))
        out.loc[values.index] = values.clip(lo, hi)
    return out


def zscore_by_date(series: pd.Series, dates: pd.Series) -> pd.Series:
    out = pd.Series(np.nan, index=series.index, dtype=float)
    work = pd.DataFrame({"date": dates, "value": series})
    for _, group in work.groupby("date"):
        values = group["value"].dropna()
        if len(values) < 20:
            continue
        std = float(values.std(ddof=1))
        if not math.isfinite(std) or std <= 0:
            continue
        mean = float(values.mean())
        out.loc[values.index] = (values - mean) / std
    return out


def add_transforms(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    raw = out["raw_score"].astype(float)
    dates = out["signal_date"]

    out["RAW_DIRECTION_NORMALIZED"] = raw
    w1 = winsorize_by_date(raw, dates, 0.01, 0.99)
    out["WINSOR_1_99"] = w1
    out["WINSOR_2_5_97_5"] = winsorize_by_date(raw, dates, 0.025, 0.975)
    out["CROSS_SECTION_ZSCORE_WINSOR_1_99"] = zscore_by_date(w1, dates)
    out["SECTOR_NEUTRAL_PERCENTILE"] = out["sector_neutral_score"]
    return out


def dated_metrics(frame: pd.DataFrame, score_col: str, horizon: int) -> dict[str, object]:
    target = f"TARGET_{horizon}"
    usable = frame[["signal_date", "ticker", score_col, target]].dropna().copy()
    ics: list[float] = []
    spreads: list[float] = []
    positive = 0

    for _, group in usable.groupby("signal_date"):
        if len(group) < 20:
            continue
        x = group[score_col].astype(float)
        y = group[target].astype(float)
        ic = x.rank().corr(y.rank())
        if pd.isna(ic):
            continue
        ic = float(ic)
        ics.append(ic)
        positive += int(ic > 0)

        ranks = x.rank(method="first")
        try:
            q = pd.qcut(ranks, 5, labels=False) + 1
        except ValueError:
            continue
        qmeans = y.groupby(q).mean()
        if 1 in qmeans.index and 5 in qmeans.index:
            spreads.append(float(qmeans.loc[5] - qmeans.loc[1]))

    mean_ic = float(np.mean(ics)) if ics else None
    std = float(np.std(ics, ddof=1)) if len(ics) > 1 else None
    return {
        "usable_cells": int(len(usable)),
        "usable_signal_dates": int(usable["signal_date"].nunique()),
        "evaluated_signal_dates": len(ics),
        "mean_ic": mean_ic,
        "ic_std": std,
        "icir": None if mean_ic is None or std in (None, 0) else mean_ic / std,
        "positive_ic_share": None if not ics else positive / len(ics),
        "mean_top_minus_bottom": float(np.mean(spreads)) if spreads else None,
    }


def stability_label(raw_ic: float | None, transformed_ic: float | None) -> str:
    if raw_ic is None or transformed_ic is None:
        return "UNAVAILABLE"
    if raw_ic == 0 or transformed_ic == 0:
        return "BORDERLINE"
    if (raw_ic > 0) != (transformed_ic > 0):
        return "SIGN_FLIP"
    delta = abs(transformed_ic - raw_ic)
    if delta <= 0.02:
        return "STABLE"
    if delta <= 0.05:
        return "MODERATE_SENSITIVITY"
    return "HIGH_SENSITIVITY"


def main() -> int:
    routes = sn.load_sector_routes()
    routes_by_ticker = {
        ticker: group.copy()
        for ticker, group in routes.groupby("ticker", sort=False)
    }
    price_panel = sn.build_price_panel(routes_by_ticker)
    financial_panel = sn.build_financial_panel(routes_by_ticker)
    frames = sn.prepare_factor_frames(price_panel, financial_panel)

    results: dict[str, object] = {}
    for factor in FACTOR_SET:
        frame = frames.get(factor)
        if frame is None:
            results[factor] = {"unavailable_reason": "FACTOR_NOT_MATERIALIZED"}
            continue
        frame = add_transforms(frame)
        factor_result: dict[str, object] = {}
        for horizon in HORIZONS:
            by_transform = {
                transform: dated_metrics(frame, transform, horizon)
                for transform in TRANSFORMS
            }
            raw_ic = by_transform["RAW_DIRECTION_NORMALIZED"]["mean_ic"]
            comparisons: dict[str, object] = {}
            for transform in TRANSFORMS[1:]:
                tic = by_transform[transform]["mean_ic"]
                comparisons[transform] = {
                    "delta_mean_ic_vs_raw": (
                        None if raw_ic is None or tic is None else float(tic - raw_ic)
                    ),
                    "stability": stability_label(raw_ic, tic),
                }
            factor_result[str(horizon)] = {
                "metrics": by_transform,
                "comparisons": comparisons,
            }
        results[factor] = factor_result

    receipt = {
        "contract": "WINSORIZATION_OUTLIER_ROBUSTNESS_DIAGNOSTIC_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "transformations": TRANSFORMS,
        "winsorization_scope": "PER_SIGNAL_DATE_ONLY",
        "pooled_full_sample_thresholds_used": False,
        "coverage": {
            "price_panel_rows": int(len(price_panel)),
            "financial_panel_rows": int(len(financial_panel)),
            "factors_requested": len(FACTOR_SET),
            "factors_materialized": sum(1 for factor in FACTOR_SET if factor in frames),
        },
        "results": results,
        "limitations": [
            "Winsorization tests magnitude sensitivity but rank IC is intrinsically less sensitive to raw-value outliers.",
            "Sector-neutral percentile is included as a comparison transform, not an outlier treatment.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK.",
            "No factor deletion, sign reversal, or weighting decision is authorized.",
        ],
    }

    out = Path("research/evidence_runs/winsor_outlier_robustness_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
