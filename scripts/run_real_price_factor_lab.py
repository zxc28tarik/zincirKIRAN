#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

TOTAL_RASYO_COMMIT = "883e680a2564e38f4c08a21bc88aa95b8f164036"
RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "zxc28tarik/TOTAL-RASYO-HESAPLAYICI/"
    f"{TOTAL_RASYO_COMMIT}/"
)
SOURCES = {
    "daily_prices": {
        "path": (
            "data/backtest_sources/yahoo_resolved/"
            "historical_member_prices_resolved_2020-07_2026-08.csv.gz"
        ),
        "sha256": "b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141",
    },
    "membership": {
        "path": (
            "data/backtest_sources/yahoo_resolved/"
            "monthly_member_signal_price_coverage.csv"
        ),
        "sha256": "a3b14014aa4d3ff16a082bc0dac64346b906f4b7720aeae5a8c449a2add314f2",
    },
    "index_closes": {
        "path": "data/backtest_sources/m3_source_package/index_closes.csv.gz",
        "sha256": "32a740f7a7114e03c885d1ae75c8bacd081b5254b043521fd76ca5f8e34e786e",
    },
}
FACTORS = (
    "HIGH_52W_PROXIMITY",
    "LIQUIDITY_63D",
    "LOW_VOL_63D",
    "MOM_12_1",
    "MOM_6_1",
)
HORIZONS = (20, 60, 120, 252)


def fetch_verified(path: str, expected_sha256: str) -> bytes:
    url = RAW_BASE + path
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    observed = hashlib.sha256(payload).hexdigest()
    if observed != expected_sha256:
        raise RuntimeError(
            f"sha256 mismatch for {path}: expected={expected_sha256} observed={observed}"
        )
    return payload


def read_csv_payload(payload: bytes, *, gzipped: bool) -> pd.DataFrame:
    if gzipped:
        payload = gzip.decompress(payload)
    return pd.read_csv(io.BytesIO(payload), low_memory=False)


def _clean_daily(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"ticker", "trade_date", "close", "adj_close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"daily price corpus missing columns: {sorted(missing)}")
    out = frame.copy()
    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    out["trade_date"] = pd.to_datetime(out["trade_date"], errors="raise")
    for col in ("close", "adj_close", "volume"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.sort_values(["ticker", "trade_date"])
    if out.duplicated(["ticker", "trade_date"]).any():
        raise RuntimeError("duplicate ticker/trade_date in daily corpus")
    return out.reset_index(drop=True)


def _clean_membership(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"signal_date", "ticker"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"membership panel missing columns: {sorted(missing)}")
    out = frame[["signal_date", "ticker"]].copy()
    out["signal_date"] = pd.to_datetime(out["signal_date"], errors="raise")
    out["ticker"] = out["ticker"].astype(str).str.upper().str.strip()
    out = out.drop_duplicates().sort_values(["signal_date", "ticker"])
    return out.reset_index(drop=True)


def _clean_index(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"index_code", "trade_date", "close"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"index close corpus missing columns: {sorted(missing)}")
    out = frame.loc[frame["index_code"].astype(str) == "XU100"].copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"], errors="raise")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out[["trade_date", "close"]].dropna().sort_values("trade_date")
    if out.duplicated("trade_date").any():
        raise RuntimeError("duplicate XU100 trade_date")
    return out.reset_index(drop=True)


def _factor_rows(
    daily: pd.DataFrame,
    membership: pd.DataFrame,
    index_frame: pd.DataFrame,
) -> pd.DataFrame:
    market_dates = index_frame["trade_date"].tolist()
    market_pos = {day: idx for idx, day in enumerate(market_dates)}
    market_close = dict(zip(index_frame["trade_date"], index_frame["close"], strict=True))

    by_ticker: dict[str, pd.DataFrame] = {
        ticker: group.reset_index(drop=True)
        for ticker, group in daily.groupby("ticker", sort=False)
    }
    by_ticker_dates = {
        ticker: {day: idx for idx, day in enumerate(group["trade_date"])}
        for ticker, group in by_ticker.items()
    }

    rows: list[dict[str, object]] = []
    for item in membership.itertuples(index=False):
        ticker = str(item.ticker)
        signal_date = pd.Timestamp(item.signal_date)
        group = by_ticker.get(ticker)
        positions = by_ticker_dates.get(ticker)
        if group is None or positions is None or signal_date not in positions:
            continue
        if signal_date not in market_pos:
            continue
        pos = positions[signal_date]
        market_idx = market_pos[signal_date]

        adj = group["adj_close"].to_numpy(dtype=float)
        close = group["close"].to_numpy(dtype=float)
        volume = group["volume"].to_numpy(dtype=float)
        if not math.isfinite(adj[pos]) or adj[pos] <= 0:
            continue

        factor_values: dict[str, float | None] = {
            factor: None for factor in FACTORS
        }

        if pos >= 252 and math.isfinite(adj[pos - 21]) and math.isfinite(adj[pos - 252]):
            if adj[pos - 21] > 0 and adj[pos - 252] > 0:
                factor_values["MOM_12_1"] = adj[pos - 21] / adj[pos - 252] - 1.0

        if pos >= 126 and math.isfinite(adj[pos - 21]) and math.isfinite(adj[pos - 126]):
            if adj[pos - 21] > 0 and adj[pos - 126] > 0:
                factor_values["MOM_6_1"] = adj[pos - 21] / adj[pos - 126] - 1.0

        if pos >= 251:
            window = adj[pos - 251 : pos + 1]
            finite = window[np.isfinite(window) & (window > 0)]
            if len(finite) == 252:
                high = float(np.max(finite))
                if high > 0:
                    factor_values["HIGH_52W_PROXIMITY"] = float(adj[pos] / high)

        if pos >= 63:
            window = adj[pos - 63 : pos + 1]
            if np.all(np.isfinite(window)) and np.all(window > 0):
                returns = window[1:] / window[:-1] - 1.0
                factor_values["LOW_VOL_63D"] = -float(np.std(returns, ddof=1))

        if pos >= 62:
            px = close[pos - 62 : pos + 1]
            vol = volume[pos - 62 : pos + 1]
            mask = np.isfinite(px) & np.isfinite(vol) & (px > 0) & (vol >= 0)
            if int(mask.sum()) == 63:
                adv = float(np.mean(px[mask] * vol[mask]))
                factor_values["LIQUIDITY_63D"] = math.log1p(max(0.0, adv))

        targets: dict[int, float | None] = {}
        for horizon in HORIZONS:
            future_market_pos = market_idx + horizon
            if future_market_pos >= len(market_dates):
                targets[horizon] = None
                continue
            future_date = market_dates[future_market_pos]
            future_stock_pos = positions.get(future_date)
            if future_stock_pos is None:
                targets[horizon] = None
                continue
            future_adj = adj[future_stock_pos]
            market_start = market_close.get(signal_date)
            market_end = market_close.get(future_date)
            if (
                not math.isfinite(future_adj)
                or future_adj <= 0
                or market_start is None
                or market_end is None
                or not math.isfinite(float(market_start))
                or not math.isfinite(float(market_end))
                or float(market_start) <= 0
            ):
                targets[horizon] = None
                continue
            stock_return = future_adj / adj[pos] - 1.0
            market_return = float(market_end) / float(market_start) - 1.0
            targets[horizon] = float(stock_return - market_return)

        row: dict[str, object] = {
            "signal_date": signal_date,
            "ticker": ticker,
        }
        row.update(factor_values)
        row.update({f"TARGET_{h}": value for h, value in targets.items()})
        rows.append(row)

    return pd.DataFrame(rows)


def _cross_section_metrics(frame: pd.DataFrame, factor: str, horizon: int) -> dict[str, float | int | None]:
    target = f"TARGET_{horizon}"
    usable = frame[["signal_date", "ticker", factor, target]].dropna().copy()
    if usable.empty:
        return {
            "usable_cells": 0,
            "usable_signal_dates": 0,
            "mean_ic": None,
            "ic_std": None,
            "icir": None,
            "mean_top_quintile_excess_return": None,
            "mean_q5_minus_q1": None,
            "mean_monotonicity": None,
        }

    ics: list[float] = []
    long_legs: list[float] = []
    spreads: list[float] = []
    monotonicity: list[float] = []

    for _, group in usable.groupby("signal_date"):
        if len(group) < 20:
            continue
        xrank = group[factor].rank(method="average")
        yrank = group[target].rank(method="average")
        ic = xrank.corr(yrank)
        if pd.notna(ic):
            ics.append(float(ic))

        ranks = group[factor].rank(method="first")
        try:
            group = group.assign(q=pd.qcut(ranks, 5, labels=False) + 1)
        except ValueError:
            continue
        qmeans = group.groupby("q")[target].mean()
        if 5 in qmeans.index:
            long_legs.append(float(qmeans.loc[5]))
        if 1 in qmeans.index and 5 in qmeans.index:
            spreads.append(float(qmeans.loc[5] - qmeans.loc[1]))
        if len(qmeans) == 5:
            qindex = pd.Series(qmeans.index.astype(float), index=qmeans.index)
            mono = qindex.corr(qmeans)
            if pd.notna(mono):
                monotonicity.append(float(mono))

    mean_ic = float(np.mean(ics)) if ics else None
    ic_std = float(np.std(ics, ddof=1)) if len(ics) > 1 else None
    icir = None
    if mean_ic is not None and ic_std is not None and ic_std > 0:
        icir = mean_ic / ic_std

    return {
        "usable_cells": int(len(usable)),
        "usable_signal_dates": int(usable["signal_date"].nunique()),
        "evaluated_signal_dates": int(len(ics)),
        "mean_ic": mean_ic,
        "ic_std": ic_std,
        "icir": icir,
        "mean_top_quintile_excess_return": (
            float(np.mean(long_legs)) if long_legs else None
        ),
        "mean_q5_minus_q1": float(np.mean(spreads)) if spreads else None,
        "mean_monotonicity": (
            float(np.mean(monotonicity)) if monotonicity else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payloads = {
        key: fetch_verified(meta["path"], meta["sha256"])
        for key, meta in SOURCES.items()
    }
    daily = _clean_daily(read_csv_payload(payloads["daily_prices"], gzipped=True))
    membership = _clean_membership(
        read_csv_payload(payloads["membership"], gzipped=False)
    )
    index_frame = _clean_index(
        read_csv_payload(payloads["index_closes"], gzipped=True)
    )
    panel = _factor_rows(daily, membership, index_frame)

    results: dict[str, dict[str, object]] = {}
    for factor in FACTORS:
        results[factor] = {}
        for horizon in HORIZONS:
            results[factor][str(horizon)] = _cross_section_metrics(
                panel,
                factor,
                horizon,
            )

    receipt = {
        "contract": "FIRST_REAL_PRICE_FACTOR_LAB_V1",
        "authority": "DIAGNOSTIC_OOS_EVIDENCE",
        "production_ready": False,
        "target": "DIAGNOSTIC_RETURN_PROXY_ADJ_CLOSE_MINUS_XU100",
        "source_commit": TOTAL_RASYO_COMMIT,
        "source_artifacts": SOURCES,
        "daily_rows": int(len(daily)),
        "membership_rows": int(len(membership)),
        "panel_rows": int(len(panel)),
        "signal_dates": int(membership["signal_date"].nunique()),
        "factors": FACTORS,
        "horizons": HORIZONS,
        "results": results,
        "limitations": [
            "Yahoo-derived adjusted close is a diagnostic total-return proxy, not official Borsa total-return truth.",
            "Historical universe is the validated 60-month BIST100 panel, not all BIST.",
            "No factor weights or thresholds were optimized from these results.",
            "Financial and analyst factors are outside this diagnostic.",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
