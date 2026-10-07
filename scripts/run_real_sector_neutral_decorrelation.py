#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import urllib.request
from itertools import combinations
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_real_financial_factor_lab as fin  # noqa: E402
import run_real_price_factor_lab as px  # noqa: E402

SOURCE_COMMIT = "445e9a7cb788124a52fd4ac171f3e16e6c67137e"
SECTOR_PATH = "data/backtest_sources/m3_source_package/sector_routes.csv.gz"
SECTOR_SHA256 = "f0c28c7babd018eb8994afdf4911a9d338dad43b291a1084a7acc47a3919c478"
RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "zxc28tarik/TOTAL-RASYO-HESAPLAYICI/"
    f"{SOURCE_COMMIT}/"
)

MIN_SECTOR_SIZE = 5
REDUNDANCY_THRESHOLD = 0.70
HORIZONS = (20, 60, 120, 252)

FINANCIAL_DIRECTIONS = {
    "asset_growth": -1.0,
    "gross_margin": 1.0,
    "gross_margin_acceleration": 1.0,
    "gross_profitability": 1.0,
    "operating_margin": 1.0,
    "operating_margin_acceleration": 1.0,
    "operating_profitability": 1.0,
    "roa": 1.0,
}
PRICE_DIRECTIONS = {
    "HIGH_52W_PROXIMITY": 1.0,
    "LIQUIDITY_63D": 1.0,
    "LOW_VOL_63D": 1.0,
    "MOM_12_1": 1.0,
    "MOM_6_1": 1.0,
}


def fetch_verified(url: str, expected_sha256: str) -> bytes:
    with urllib.request.urlopen(url, timeout=180) as response:
        payload = response.read()
    observed = hashlib.sha256(payload).hexdigest()
    if observed != expected_sha256:
        raise RuntimeError(
            f"sha256 mismatch expected={expected_sha256} observed={observed}"
        )
    return payload


def load_sector_routes() -> pd.DataFrame:
    payload = fetch_verified(RAW_BASE + SECTOR_PATH, SECTOR_SHA256)
    frame = pd.read_csv(io.BytesIO(gzip.decompress(payload)), low_memory=False)
    required = {"ticker", "valid_from", "valid_to", "sector_index_code"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"sector routes missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["ticker"] = frame["ticker"].astype(str).str.upper().str.strip()
    frame["valid_from"] = pd.to_datetime(frame["valid_from"], errors="raise")
    frame["valid_to"] = pd.to_datetime(frame["valid_to"], errors="coerce")
    frame["sector_index_code"] = frame["sector_index_code"].astype(str).str.strip()
    return frame.sort_values(["ticker", "valid_from"]).reset_index(drop=True)


def sector_for(
    routes_by_ticker: dict[str, pd.DataFrame],
    ticker: str,
    signal_date: pd.Timestamp,
) -> str | None:
    rows = routes_by_ticker.get(ticker)
    if rows is None:
        return None
    eligible = rows.loc[
        rows["valid_from"].le(signal_date)
        & (rows["valid_to"].isna() | rows["valid_to"].gt(signal_date))
    ]
    if len(eligible) != 1:
        return None
    value = str(eligible.iloc[0]["sector_index_code"]).strip()
    return value or None


def build_price_panel(
    routes_by_ticker: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    daily_payload = px.fetch_verified(
        px.SOURCES["daily_prices"]["path"],
        px.SOURCES["daily_prices"]["sha256"],
    )
    membership_payload = px.fetch_verified(
        px.SOURCES["membership"]["path"],
        px.SOURCES["membership"]["sha256"],
    )
    index_payload = px.fetch_verified(
        px.SOURCES["index_closes"]["path"],
        px.SOURCES["index_closes"]["sha256"],
    )
    daily = px._clean_daily(px.read_csv_payload(daily_payload, gzipped=True))
    membership = px._clean_membership(
        px.read_csv_payload(membership_payload, gzipped=False)
    )
    index_frame = px._clean_index(
        px.read_csv_payload(index_payload, gzipped=True)
    )
    panel = px._factor_rows(daily, membership, index_frame)
    panel["signal_date"] = pd.to_datetime(panel["signal_date"])
    panel["ticker"] = panel["ticker"].astype(str).str.upper()
    panel["sector"] = [
        sector_for(routes_by_ticker, ticker, signal)
        for ticker, signal in zip(panel["ticker"], panel["signal_date"], strict=True)
    ]
    return panel


def build_financial_panel(
    routes_by_ticker: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    semantic = fin.iter_semantic()
    prices = fin.csv_from_market("prices")
    membership = fin.csv_from_market("membership")
    index = fin.csv_from_market("index")
    membership["signal_date"] = pd.to_datetime(membership["signal_date"])
    membership["ticker"] = membership["ticker"].astype(str).str.upper()
    membership = membership[["signal_date", "ticker"]].drop_duplicates()

    rows_by_ticker: dict[str, list[dict]] = {}
    for row in semantic:
        mapped = str(row.get("report_mapping_ticker") or "").strip().upper()
        fact_tickers = {
            str(f.get("ticker") or "").strip().upper()
            for f in row.get("facts") or []
            if f.get("ticker")
        }
        targets = {mapped} if mapped else fact_tickers
        for ticker in targets:
            if ticker:
                rows_by_ticker.setdefault(ticker, []).append(row)

    targets = fin.forward_targets(prices, index, membership)
    panel_rows: list[dict[str, object]] = []
    for item in membership.itertuples(index=False):
        signal_ts = pd.Timestamp(item.signal_date)
        signal = signal_ts.date()
        ticker = str(item.ticker).upper()
        fact_rows = rows_by_ticker.get(ticker)
        if not fact_rows:
            continue
        by_field = fin.latest_fact_map(fact_rows, signal, ticker)
        factors = fin.materialize_financial_factors(by_field, signal)
        if not factors:
            continue
        row: dict[str, object] = {
            "signal_date": signal_ts,
            "ticker": ticker,
            "sector": sector_for(routes_by_ticker, ticker, signal_ts),
        }
        row.update(factors)
        for horizon, value in targets.get((signal, ticker), {}).items():
            row[f"TARGET_{horizon}"] = value
        panel_rows.append(row)
    return pd.DataFrame(panel_rows)


def sector_neutralize(
    panel: pd.DataFrame,
    factor: str,
    *,
    direction: float,
) -> pd.Series:
    score = pd.Series(np.nan, index=panel.index, dtype=float)
    usable = panel.loc[
        panel[factor].notna() & panel["sector"].notna(),
        ["signal_date", "sector", factor],
    ].copy()
    usable["_directed"] = usable[factor].astype(float) * direction
    for _, group in usable.groupby(["signal_date", "sector"], sort=True):
        if len(group) < MIN_SECTOR_SIZE:
            continue
        pct = group["_directed"].rank(method="average", pct=True)
        score.loc[group.index] = pct - 0.5
    return score


def raw_score(panel: pd.DataFrame, factor: str, direction: float) -> pd.Series:
    return panel[factor].astype(float) * direction


def evaluate_score(
    panel: pd.DataFrame,
    score_col: str,
    horizon: int,
) -> dict[str, object]:
    target = f"TARGET_{horizon}"
    if target not in panel or score_col not in panel:
        return {
            "usable_cells": 0,
            "evaluated_signal_dates": 0,
            "mean_ic": None,
            "icir": None,
            "mean_top_minus_bottom": None,
        }
    usable = panel[["signal_date", "ticker", score_col, target]].dropna().copy()
    ics: list[float] = []
    spreads: list[float] = []
    tops: list[float] = []
    for _, group in usable.groupby("signal_date"):
        if len(group) < 20:
            continue
        x = group[score_col].astype(float)
        y = group[target].astype(float)
        ic = x.rank().corr(y.rank())
        if pd.notna(ic):
            ics.append(float(ic))
        ranks = x.rank(method="first")
        try:
            q = pd.qcut(ranks, 5, labels=False) + 1
        except ValueError:
            continue
        qmeans = y.groupby(q).mean()
        if 5 in qmeans.index:
            tops.append(float(qmeans.loc[5]))
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
        "mean_top_quintile_excess_return": (
            float(np.mean(tops)) if tops else None
        ),
        "mean_top_minus_bottom": float(np.mean(spreads)) if spreads else None,
    }


def pairwise_sector_neutral_correlations(
    frames: dict[str, pd.DataFrame],
) -> list[dict[str, object]]:
    long_rows: list[pd.DataFrame] = []
    for factor, frame in frames.items():
        usable = frame[
            ["signal_date", "ticker", "sector_neutral_score"]
        ].dropna().copy()
        usable["factor"] = factor
        long_rows.append(usable)
    combined = pd.concat(long_rows, ignore_index=True)

    results: list[dict[str, object]] = []
    factors = sorted(frames)
    for left, right in combinations(factors, 2):
        dated: list[float] = []
        overlaps: list[int] = []
        for signal, group in combined.loc[
            combined["factor"].isin([left, right])
        ].groupby("signal_date"):
            pivot = group.pivot_table(
                index="ticker",
                columns="factor",
                values="sector_neutral_score",
                aggfunc="first",
            )
            if left not in pivot or right not in pivot:
                continue
            pair = pivot[[left, right]].dropna()
            if len(pair) < 20:
                continue
            rho = pair[left].rank().corr(pair[right].rank())
            if pd.notna(rho):
                dated.append(float(rho))
                overlaps.append(int(len(pair)))
        mean_rho = float(np.mean(dated)) if dated else None
        results.append(
            {
                "left": left,
                "right": right,
                "mean_spearman": mean_rho,
                "mean_overlap": (
                    float(np.mean(overlaps)) if overlaps else None
                ),
                "valid_dates": len(dated),
                "redundancy_candidate": (
                    mean_rho is not None
                    and abs(mean_rho) >= REDUNDANCY_THRESHOLD
                ),
            }
        )
    return results


def prepare_factor_frames(
    price_panel: pd.DataFrame,
    financial_panel: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for factor, direction in PRICE_DIRECTIONS.items():
        if factor not in price_panel:
            continue
        frame = price_panel.copy()
        frame["raw_score"] = raw_score(frame, factor, direction)
        frame["sector_neutral_score"] = sector_neutralize(
            frame,
            factor,
            direction=direction,
        )
        frames[factor] = frame

    for factor, direction in FINANCIAL_DIRECTIONS.items():
        if factor not in financial_panel:
            continue
        frame = financial_panel.copy()
        frame["raw_score"] = raw_score(frame, factor, direction)
        frame["sector_neutral_score"] = sector_neutralize(
            frame,
            factor,
            direction=direction,
        )
        frames[factor] = frame
    return frames


def main() -> int:
    routes = load_sector_routes()
    routes_by_ticker = {
        ticker: group.copy()
        for ticker, group in routes.groupby("ticker", sort=False)
    }
    price_panel = build_price_panel(routes_by_ticker)
    financial_panel = build_financial_panel(routes_by_ticker)
    frames = prepare_factor_frames(price_panel, financial_panel)

    evaluations: dict[str, dict[str, object]] = {}
    for factor, frame in sorted(frames.items()):
        evaluations[factor] = {}
        for horizon in HORIZONS:
            evaluations[factor][str(horizon)] = {
                "raw": evaluate_score(frame, "raw_score", horizon),
                "sector_neutral": evaluate_score(
                    frame,
                    "sector_neutral_score",
                    horizon,
                ),
            }

    correlations = pairwise_sector_neutral_correlations(frames)
    redundancy = [
        row for row in correlations if row["redundancy_candidate"]
    ]

    receipt = {
        "contract": "REAL_SECTOR_NEUTRAL_DECORRELATION_DIAGNOSTIC_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "sector_route_source": {
            "commit": SOURCE_COMMIT,
            "path": SECTOR_PATH,
            "sha256": SECTOR_SHA256,
            "rows": int(len(routes)),
        },
        "method": {
            "direction_normalized": True,
            "within_sector_transform": "PERCENTILE_RANK_MINUS_0_5",
            "minimum_sector_size": MIN_SECTOR_SIZE,
            "redundancy_method": "MEAN_WITHIN_DATE_SPEARMAN",
            "redundancy_absolute_threshold": REDUNDANCY_THRESHOLD,
        },
        "coverage": {
            "price_panel_rows": int(len(price_panel)),
            "financial_panel_rows": int(len(financial_panel)),
            "price_rows_with_sector": int(price_panel["sector"].notna().sum()),
            "financial_rows_with_sector": int(financial_panel["sector"].notna().sum()),
            "factor_count": len(frames),
        },
        "evaluations": evaluations,
        "pairwise_sector_neutral_correlations": correlations,
        "redundancy_candidates": redundancy,
        "limitations": [
            "Sector groups are the date-valid broad historical Borsa/KAP routes XUSIN/XUHIZ/XUMAL/XUTEK, not fine industry groups.",
            "Financial factors retain EXPERIMENTAL_VERSION_RISK due incomplete superseded-report enumeration.",
            "Future return labels use Yahoo adjusted-close minus XU100 as a diagnostic proxy.",
            "Sector neutralization and redundancy evidence do not authorize factor deletion or weight changes.",
        ],
    }
    out = Path(
        "research/evidence_runs/"
        "real_sector_neutral_decorrelation_diagnostic_v1.json"
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
