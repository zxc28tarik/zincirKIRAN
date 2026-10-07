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
MIN_PERIOD_MONTHS = 6

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

BREAKPOINTS = {
    "calendar_2024": pd.Timestamp("2024-01-01"),
    "transition_2024_04": pd.Timestamp("2024-04-01"),
}


def dated_ic(
    frame: pd.DataFrame,
    score_col: str,
    horizon: int,
) -> pd.DataFrame:
    target = f"TARGET_{horizon}"
    usable = frame[["signal_date", "ticker", score_col, target]].dropna().copy()
    rows: list[dict[str, object]] = []
    for signal_date, group in usable.groupby("signal_date"):
        if len(group) < 20:
            continue
        x = group[score_col].astype(float)
        y = group[target].astype(float)
        ic = x.rank().corr(y.rank())
        if pd.isna(ic):
            continue
        rows.append(
            {
                "signal_date": pd.Timestamp(signal_date),
                "ic": float(ic),
                "n": int(len(group)),
            }
        )
    return pd.DataFrame(rows).sort_values("signal_date").reset_index(drop=True)


def summarize_period(series: pd.DataFrame) -> dict[str, object]:
    if series.empty or len(series) < MIN_PERIOD_MONTHS:
        return {
            "valid_months": int(len(series)),
            "mean_ic": None,
            "ic_std": None,
            "icir": None,
            "positive_ic_share": None,
            "unavailable_reason": "INSUFFICIENT_VALID_MONTHS",
        }
    values = series["ic"].astype(float).to_numpy()
    mean_ic = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else None
    return {
        "valid_months": int(len(values)),
        "mean_ic": mean_ic,
        "ic_std": std,
        "icir": None if std in (None, 0) else mean_ic / std,
        "positive_ic_share": float(np.mean(values > 0)),
    }


def split_summary(
    series: pd.DataFrame,
    breakpoint: pd.Timestamp,
) -> dict[str, object]:
    pre = series.loc[series["signal_date"].lt(breakpoint)].copy()
    post = series.loc[series["signal_date"].ge(breakpoint)].copy()
    pre_summary = summarize_period(pre)
    post_summary = summarize_period(post)
    delta = None
    if pre_summary["mean_ic"] is not None and post_summary["mean_ic"] is not None:
        delta = float(post_summary["mean_ic"] - pre_summary["mean_ic"])
    return {
        "breakpoint": breakpoint.date().isoformat(),
        "pre": pre_summary,
        "post": post_summary,
        "post_minus_pre_mean_ic": delta,
    }


def annual_summary(series: pd.DataFrame) -> dict[str, object]:
    out: dict[str, object] = {}
    if series.empty:
        return out
    work = series.copy()
    work["year"] = work["signal_date"].dt.year
    for year, group in work.groupby("year"):
        if int(year) < 2022:
            continue
        out[str(int(year))] = summarize_period(group.drop(columns=["year"]))
    return out


def factor_time_diagnostics(
    frame: pd.DataFrame,
    factor: str,
) -> dict[str, object]:
    result: dict[str, object] = {}
    for horizon in HORIZONS:
        result[str(horizon)] = {}
        for score_col, label in (
            ("raw_score", "raw"),
            ("sector_neutral_score", "sector_neutral"),
        ):
            series = dated_ic(frame, score_col, horizon)
            result[str(horizon)][label] = {
                "full": summarize_period(series),
                "splits": {
                    key: split_summary(series, bp)
                    for key, bp in BREAKPOINTS.items()
                },
                "annual": annual_summary(series),
            }
    return result


def main() -> int:
    routes = sn.load_sector_routes()
    routes_by_ticker = {
        ticker: group.copy()
        for ticker, group in routes.groupby("ticker", sort=False)
    }
    price_panel = sn.build_price_panel(routes_by_ticker)
    financial_panel = sn.build_financial_panel(routes_by_ticker)
    frames = sn.prepare_factor_frames(price_panel, financial_panel)

    diagnostics: dict[str, object] = {}
    for factor in FACTOR_SET:
        frame = frames.get(factor)
        if frame is None:
            diagnostics[factor] = {
                "unavailable_reason": "FACTOR_NOT_MATERIALIZED"
            }
            continue
        diagnostics[factor] = factor_time_diagnostics(frame, factor)

    receipt = {
        "contract": "ACCOUNTING_REGIME_SUBPERIOD_DIAGNOSTIC_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "tms29_observation_level_flag_available": False,
        "regime_classification": "CALENDAR_PROXY_ONLY",
        "breakpoints": {
            key: value.date().isoformat()
            for key, value in BREAKPOINTS.items()
        },
        "minimum_valid_months_per_subperiod": MIN_PERIOD_MONTHS,
        "coverage": {
            "price_panel_rows": int(len(price_panel)),
            "financial_panel_rows": int(len(financial_panel)),
            "factor_count_requested": len(FACTOR_SET),
            "factor_count_materialized": sum(
                1 for factor in FACTOR_SET if factor in frames
            ),
        },
        "diagnostics": diagnostics,
        "limitations": [
            "No authoritative per-observation TMS29/inflation-adjusted flag exists in the current semantic corpus.",
            "2024-01 and 2024-04 breakpoints are calendar research proxies, not company-level accounting-regime labels.",
            "Financial inputs retain EXPERIMENTAL_VERSION_RISK from incomplete superseded-version enumeration.",
            "Sector-neutralization uses broad historical sector routes only.",
            "Forward returns remain the adjusted-close-minus-XU100 diagnostic proxy.",
        ],
    }
    out = Path(
        "research/evidence_runs/"
        "accounting_regime_subperiod_diagnostic_v1.json"
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
