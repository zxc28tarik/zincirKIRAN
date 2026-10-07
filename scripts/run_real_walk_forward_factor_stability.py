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

CANDIDATES = (
    "HIGH_52W_PROXIMITY",
    "LOW_VOL_63D",
    "MOM_6_1",
    "operating_margin_acceleration",
    "gross_margin_acceleration",
    "asset_growth",
)
HORIZONS = (20, 60, 120, 252)
TEST_BLOCK_MONTHS = 6
MIN_INITIAL_TRAIN_MONTHS = 18
MIN_TEST_MONTHS = 3


def build_panels() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    routes = sn.load_sector_routes()
    routes_by_ticker = {
        ticker: group.copy()
        for ticker, group in routes.groupby("ticker", sort=False)
    }
    price_panel = sn.build_price_panel(routes_by_ticker)
    financial_panel = sn.build_financial_panel(routes_by_ticker)
    frames = sn.prepare_factor_frames(price_panel, financial_panel)

    index = sn.fin.csv_from_market("index")
    xu = index.loc[index["index_code"].astype(str).eq("XU100")].copy()
    xu["trade_date"] = pd.to_datetime(xu["trade_date"])
    xu = xu.sort_values("trade_date").reset_index(drop=True)
    return frames, xu


def maturity_map(
    signal_dates: list[pd.Timestamp],
    trading_calendar: pd.DataFrame,
    horizon: int,
) -> dict[pd.Timestamp, pd.Timestamp | None]:
    dates = trading_calendar["trade_date"].tolist()
    pos = {pd.Timestamp(day): i for i, day in enumerate(dates)}
    out: dict[pd.Timestamp, pd.Timestamp | None] = {}
    for signal in signal_dates:
        signal = pd.Timestamp(signal)
        start = pos.get(signal)
        if start is None or start + horizon >= len(dates):
            out[signal] = None
        else:
            out[signal] = pd.Timestamp(dates[start + horizon])
    return out


def month_blocks(signal_dates: list[pd.Timestamp]) -> list[list[pd.Timestamp]]:
    ordered = sorted(pd.Timestamp(x) for x in signal_dates)
    blocks: list[list[pd.Timestamp]] = []
    for start in range(MIN_INITIAL_TRAIN_MONTHS, len(ordered), TEST_BLOCK_MONTHS):
        block = ordered[start : start + TEST_BLOCK_MONTHS]
        if len(block) >= MIN_TEST_MONTHS:
            blocks.append(block)
    return blocks


def dated_factor_ic(
    frame: pd.DataFrame,
    horizon: int,
    score_col: str,
) -> pd.DataFrame:
    target = f"TARGET_{horizon}"
    usable = frame[["signal_date", "ticker", score_col, target]].dropna().copy()
    rows: list[dict[str, object]] = []
    for signal, group in usable.groupby("signal_date"):
        if len(group) < 20:
            continue
        x = group[score_col].astype(float)
        y = group[target].astype(float)
        ic = x.rank().corr(y.rank())
        if pd.isna(ic):
            continue
        ranks = x.rank(method="first")
        spread = None
        try:
            q = pd.qcut(ranks, 5, labels=False) + 1
            means = y.groupby(q).mean()
            if 1 in means.index and 5 in means.index:
                spread = float(means.loc[5] - means.loc[1])
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
    return pd.DataFrame(rows).sort_values("signal_date").reset_index(drop=True)


def summarize_months(rows: pd.DataFrame) -> dict[str, object]:
    if rows.empty:
        return {
            "months": 0,
            "mean_ic": None,
            "ic_std": None,
            "icir": None,
            "positive_ic_share": None,
            "mean_top_minus_bottom": None,
        }
    vals = rows["ic"].astype(float).to_numpy()
    std = float(np.std(vals, ddof=1)) if len(vals) > 1 else None
    spreads = rows["spread"].dropna().astype(float).to_numpy()
    mean_ic = float(np.mean(vals))
    return {
        "months": int(len(vals)),
        "mean_ic": mean_ic,
        "ic_std": std,
        "icir": None if std in (None, 0) else mean_ic / std,
        "positive_ic_share": float(np.mean(vals > 0)),
        "mean_top_minus_bottom": (
            float(np.mean(spreads)) if len(spreads) else None
        ),
    }


def classify_stability(
    fold_ics: list[float],
    *,
    mean_ic: float | None,
) -> str:
    if not fold_ics or mean_ic is None:
        return "UNAVAILABLE"
    positive_share = sum(value > 0 for value in fold_ics) / len(fold_ics)
    worst = min(fold_ics)
    if positive_share >= 0.75 and mean_ic >= 0.05 and worst >= -0.05:
        return "STRONG_STABILITY"
    if positive_share >= 0.60 and mean_ic > 0 and worst >= -0.10:
        return "MODERATE_STABILITY"
    if mean_ic > 0:
        return "FRAGILE_POSITIVE"
    return "UNSTABLE_OR_NEGATIVE"


def run_factor_horizon(
    frame: pd.DataFrame,
    calendar: pd.DataFrame,
    factor: str,
    horizon: int,
    score_col: str,
) -> dict[str, object]:
    monthly = dated_factor_ic(frame, horizon, score_col)
    if monthly.empty:
        return {"unavailable_reason": "NO_VALID_MONTHLY_IC"}

    signal_dates = sorted(pd.Timestamp(x) for x in frame["signal_date"].dropna().unique())
    maturity = maturity_map(signal_dates, calendar, horizon)
    folds: list[dict[str, object]] = []

    for fold_idx, test_dates in enumerate(month_blocks(signal_dates), start=1):
        test_start = min(test_dates)
        test_end = max(test_dates)

        train_dates = [
            signal for signal in signal_dates
            if signal < test_start
            and maturity.get(signal) is not None
            and maturity[signal] < test_start
        ]
        if len(train_dates) < MIN_INITIAL_TRAIN_MONTHS:
            continue

        test_rows = monthly.loc[monthly["signal_date"].isin(test_dates)].copy()
        train_rows = monthly.loc[monthly["signal_date"].isin(train_dates)].copy()
        if len(test_rows) < MIN_TEST_MONTHS:
            continue

        train_summary = summarize_months(train_rows)
        test_summary = summarize_months(test_rows)
        folds.append(
            {
                "fold_id": f"{factor}-H{horizon}-F{fold_idx}",
                "train_start": min(train_dates).date().isoformat(),
                "train_end": max(train_dates).date().isoformat(),
                "train_last_label_maturity": max(
                    maturity[signal] for signal in train_dates if maturity[signal] is not None
                ).date().isoformat(),
                "validation_start": test_start.date().isoformat(),
                "validation_end": test_end.date().isoformat(),
                "horizon_trading_days": horizon,
                "train": train_summary,
                "test": test_summary,
                "purge_verified_by_label_maturity": True,
            }
        )

    fold_ics = [
        float(fold["test"]["mean_ic"])
        for fold in folds
        if fold["test"]["mean_ic"] is not None
    ]
    mean_test_ic = float(np.mean(fold_ics)) if fold_ics else None
    worst_fold = min(fold_ics) if fold_ics else None
    positive_fold_share = (
        sum(value > 0 for value in fold_ics) / len(fold_ics)
        if fold_ics else None
    )
    early_late_delta = None
    if len(fold_ics) >= 2:
        early_late_delta = fold_ics[-1] - fold_ics[0]

    return {
        "fold_count": len(folds),
        "folds": folds,
        "mean_test_ic": mean_test_ic,
        "worst_fold_ic": worst_fold,
        "positive_test_fold_share": positive_fold_share,
        "late_minus_early_fold_ic": early_late_delta,
        "stability": classify_stability(fold_ics, mean_ic=mean_test_ic),
    }


def main() -> int:
    frames, calendar = build_panels()
    results: dict[str, object] = {}

    for factor in CANDIDATES:
        frame = frames.get(factor)
        if frame is None:
            results[factor] = {"unavailable_reason": "FACTOR_NOT_MATERIALIZED"}
            continue
        by_horizon: dict[str, object] = {}
        for horizon in HORIZONS:
            by_horizon[str(horizon)] = {
                "sector_neutral": run_factor_horizon(
                    frame,
                    calendar,
                    factor,
                    horizon,
                    "sector_neutral_score",
                ),
                "raw": run_factor_horizon(
                    frame,
                    calendar,
                    factor,
                    horizon,
                    "raw_score",
                ),
            }
        results[factor] = by_horizon

    receipt = {
        "contract": "REAL_WALK_FORWARD_FACTOR_STABILITY_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "candidate_factors": CANDIDATES,
        "horizons": HORIZONS,
        "design": {
            "chronological_only": True,
            "random_split": False,
            "test_block_months": TEST_BLOCK_MONTHS,
            "minimum_initial_train_months": MIN_INITIAL_TRAIN_MONTHS,
            "minimum_test_months": MIN_TEST_MONTHS,
            "purge_rule": "TRAIN_LABEL_MATURITY_STRICTLY_BEFORE_VALIDATION_START",
            "expanding_train": True,
            "hyperparameter_tuning": False,
            "primary_score": "SECTOR_NEUTRAL",
            "raw_score_comparison_retained": True,
        },
        "results": results,
        "limitations": [
            "This is factor stability evidence, not a portfolio champion/challenger promotion.",
            "Validation blocks are chronological monthly blocks; no factor parameters are trained or tuned.",
            "Long-horizon H252 naturally has fewer valid folds because labels must mature before each validation start.",
            "Financial factors remain EXPERIMENTAL_VERSION_RISK.",
            "Future returns remain the adjusted-close-minus-XU100 diagnostic proxy.",
        ],
    }
    out = Path("research/evidence_runs/real_walk_forward_factor_stability_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
