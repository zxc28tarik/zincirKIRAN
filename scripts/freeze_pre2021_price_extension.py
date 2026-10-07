#!/usr/bin/env python3
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import reconstruct_bist100_membership_backcast as backcast  # noqa: E402
import run_pre2021_coverage_power_audit as audit  # noqa: E402
import run_real_financial_factor_lab as fin  # noqa: E402
import run_real_sector_neutral_decorrelation as sn  # noqa: E402

OUT = ROOT / "data/research_sources/pre2021_price_extension_v1"
START_MONTH = "2020-09"
END_MONTH = "2021-07"
FETCH_START = "2018-01-01"
FETCH_END = "2022-09-01"
MIN_ROWS = 20

LINEAGE_REPO = "zxc28tarik/TOTAL-RASYO-HESAPLAYICI"
LINEAGE_COMMIT = "883e680a2564e38f4c08a21bc88aa95b8f164036"
LINEAGE_PATH = "data/backtest_sources/bist_ticker_code_changes_2021-08_2026-08.csv"
LINEAGE_URL = (
    "https://raw.githubusercontent.com/"
    f"{LINEAGE_REPO}/{LINEAGE_COMMIT}/{LINEAGE_PATH}"
)
OFFICIAL_WORKBOOK_SHA256 = (
    "cb5e2fc5ed8bd69b75db7707f0078facc3b900ae14cb51e8f3a286e13cf239b5"
)
ALLOWED_ALIAS_TARGETS = {
    "DGKLB": "DGNMO",
    "ITTFH": "LRSHO",
    "IPEKE": "TRENJ",
    "KERVT": "BESLR",
    "KOZAA": "TRMET",
    "KOZAL": "TRALT",
}
CURRENCY = "TRY"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_url(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def load_official_lineage() -> dict[str, dict[str, str]]:
    payload = fetch_url(LINEAGE_URL)
    frame = pd.read_csv(io.BytesIO(payload), dtype=str, keep_default_na=False)
    required = {
        "effective_date",
        "old_ticker",
        "new_ticker",
        "source_workbook_sha256",
        "event_sha256",
    }
    if required - set(frame.columns):
        raise RuntimeError("official lineage source missing required columns")

    selected: dict[str, dict[str, str]] = {}
    for old, expected_new in ALLOWED_ALIAS_TARGETS.items():
        rows = frame.loc[
            frame["old_ticker"].str.upper().eq(old)
            & frame["new_ticker"].str.upper().eq(expected_new)
        ]
        if len(rows) != 1:
            raise RuntimeError(
                f"expected exactly one official lineage row {old}->{expected_new}; found {len(rows)}"
            )
        row = rows.iloc[0].to_dict()
        if row["source_workbook_sha256"].lower() != OFFICIAL_WORKBOOK_SHA256:
            raise RuntimeError(f"official workbook hash mismatch for {old}->{expected_new}")
        selected[old] = {
            "old_ticker": old,
            "new_ticker": expected_new,
            "effective_date": row["effective_date"],
            "source_workbook_sha256": row["source_workbook_sha256"].lower(),
            "event_sha256": row["event_sha256"].lower(),
        }
    return selected


def normalize_history(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(
            columns=[
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
            ]
        )
    out = frame.copy().reset_index()
    date_col = "Date" if "Date" in out.columns else out.columns[0]
    dates = pd.to_datetime(out[date_col], errors="coerce")
    try:
        dates = dates.dt.tz_localize(None)
    except TypeError:
        dates = dates.dt.tz_convert(None)
    out["trade_date"] = dates.dt.normalize()

    for source, target in (
        ("Open", "open"),
        ("High", "high"),
        ("Low", "low"),
        ("Close", "close"),
        ("Adj Close", "adj_close"),
        ("Volume", "volume"),
    ):
        out[target] = (
            pd.to_numeric(out[source], errors="coerce")
            if source in out.columns
            else np.nan
        )
    if out["adj_close"].isna().all():
        out["adj_close"] = out["close"]

    return (
        out[
            [
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
            ]
        ]
        .dropna(subset=["trade_date"])
        .sort_values("trade_date")
        .drop_duplicates("trade_date", keep="last")
        .reset_index(drop=True)
    )


def fetch_symbol(symbol: str, attempts: int = 4) -> tuple[pd.DataFrame, str | None]:
    last: str | None = None
    for attempt in range(attempts):
        try:
            raw = yf.Ticker(symbol).history(
                start=FETCH_START,
                end=FETCH_END,
                auto_adjust=False,
                actions=False,
                repair=False,
                raise_errors=True,
            )
            frame = normalize_history(raw)
            if not frame.empty:
                return frame, None
            last = "EMPTY"
        except Exception as exc:
            last = repr(exc)
        time.sleep(0.8 * (attempt + 1))
    return normalize_history(pd.DataFrame()), last


def load_membership() -> tuple[pd.DataFrame, pd.DataFrame]:
    frozen_index = audit.load_frozen_index_calendar()
    months = pd.period_range(START_MONTH, END_MONTH, freq="M")
    tmp = frozen_index.copy()
    tmp["month"] = tmp["trade_date"].dt.to_period("M")
    signals: list[pd.Timestamp] = []
    for month in months:
        rows = tmp.loc[tmp["month"] == month].sort_values("trade_date")
        if rows.empty:
            raise RuntimeError(f"frozen XU100 calendar missing month {month}")
        signals.append(pd.Timestamp(rows.iloc[0]["trade_date"]))

    earliest, events = audit.load_membership_events()
    membership = audit.monthly_membership(earliest, events, signals)
    counts = membership.groupby("signal_date")["ticker"].nunique()
    if len(counts) != len(months) or not counts.eq(100).all():
        raise RuntimeError(f"membership is not exactly 100 names/month: {counts.to_dict()}")
    return membership.sort_values(["signal_date", "ticker"]).reset_index(drop=True), frozen_index


def direct_fetch(
    tickers: list[str],
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    histories: dict[str, pd.DataFrame] = {}
    failures: dict[str, str] = {}

    def one(ticker: str) -> tuple[str, pd.DataFrame, str | None]:
        frame, err = fetch_symbol(f"{ticker}.IS")
        return ticker, frame, err

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(one, ticker) for ticker in tickers]
        for future in as_completed(futures):
            ticker, frame, err = future.result()
            if frame.empty:
                failures[ticker] = err or "EMPTY"
            else:
                histories[ticker] = frame
    return histories, failures


def resolve_aliases(
    histories: dict[str, pd.DataFrame],
    failures: dict[str, str],
    official: dict[str, dict[str, str]],
    target_tickers: set[str],
) -> tuple[dict[str, pd.DataFrame], list[dict[str, object]], dict[str, str]]:
    resolved = dict(histories)
    audits: list[dict[str, object]] = []
    remaining = dict(failures)

    candidates = [
        old
        for old in sorted(ALLOWED_ALIAS_TARGETS)
        if old in target_tickers and old not in resolved
    ]
    for old in candidates:
        meta = official[old]
        new = meta["new_ticker"]
        source, err = fetch_symbol(f"{new}.IS")
        if source.empty:
            remaining[old] = f"ALIAS_SOURCE_FAILED {new}: {err}"
            audits.append(
                {
                    **meta,
                    "status": "ALIAS_SOURCE_FAILED",
                    "recovered_rows": 0,
                    "source_symbol": f"{new}.IS",
                    "error": err,
                }
            )
            continue

        # These are explicit code changes for the same listed identity. For
        # pre-change research signals we keep the historical signal ticker as
        # canonical identity across the full fetch window so forward H252
        # endpoints remain continuous across the later code-change date.
        canon = source.copy()
        canon["source_ticker"] = new
        canon["price_resolution"] = "OFFICIAL_BORSA_CODE_LINEAGE_YAHOO"
        canon["alias_effective_date"] = pd.Timestamp(meta["effective_date"])
        resolved[old] = canon
        remaining.pop(old, None)
        audits.append(
            {
                **meta,
                "status": "RESOLVED",
                "recovered_rows": int(len(canon)),
                "source_symbol": f"{new}.IS",
                "error": None,
            }
        )

    return resolved, audits, remaining


def canonical_rows(
    resolved: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for ticker, frame in sorted(resolved.items()):
        if frame.empty:
            continue
        part = frame.copy()
        if "source_ticker" not in part:
            part["source_ticker"] = ticker
        if "price_resolution" not in part:
            part["price_resolution"] = "DIRECT_YAHOO"
        if "alias_effective_date" not in part:
            part["alias_effective_date"] = pd.NaT
        part["ticker"] = ticker
        part["currency"] = CURRENCY
        rows.append(
            part[
                [
                    "ticker",
                    "source_ticker",
                    "price_resolution",
                    "alias_effective_date",
                    "trade_date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "adj_close",
                    "volume",
                    "currency",
                ]
            ]
        )
    if not rows:
        raise RuntimeError("no canonical price rows")
    out = pd.concat(rows, ignore_index=True)
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.normalize()
    out["alias_effective_date"] = pd.to_datetime(
        out["alias_effective_date"], errors="coerce"
    ).dt.normalize()
    if out.duplicated(["ticker", "trade_date"]).any():
        dup = out.loc[
            out.duplicated(["ticker", "trade_date"], keep=False),
            ["ticker", "trade_date"],
        ]
        raise RuntimeError(f"duplicate canonical ticker/date: {dup.head().to_dict('records')}")
    return out.sort_values(["ticker", "trade_date"]).reset_index(drop=True)


def write_deterministic_gzip_csv(frame: pd.DataFrame, path: Path) -> str:
    text = frame.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d")
    payload = gzip.compress(text.encode("utf-8"), compresslevel=9, mtime=0)
    path.write_bytes(payload)
    return sha256_bytes(payload)


def coverage_check(
    membership: pd.DataFrame,
    canonical: pd.DataFrame,
    frozen_index: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    by_ticker = {
        ticker: group[
            ["trade_date", "open", "high", "low", "close", "adj_close", "volume"]
        ].sort_values("trade_date").reset_index(drop=True)
        for ticker, group in canonical.groupby("ticker")
    }
    market_dates = [pd.Timestamp(x) for x in frozen_index["trade_date"]]
    market_pos = {day: i for i, day in enumerate(market_dates)}

    financial_index = audit.build_financial_index()
    routes = sn.load_sector_routes()
    routes_by_ticker = {
        ticker: group.copy()
        for ticker, group in routes.groupby("ticker", sort=False)
    }

    rows: list[dict[str, object]] = []
    for item in membership.itertuples(index=False):
        signal = pd.Timestamp(item.signal_date)
        ticker = str(item.ticker)
        market = audit.factor_market_values(
            by_ticker.get(ticker, pd.DataFrame()),
            signal,
            market_dates,
            market_pos,
        )

        factors: dict[str, float] = {}
        fact_rows = financial_index.get(ticker)
        if fact_rows:
            by_field = fin.latest_fact_map(fact_rows, signal.date(), ticker)
            factors = fin.materialize_financial_factors(by_field, signal.date())

        rows.append(
            {
                "signal_date": signal,
                "ticker": ticker,
                "sector": sn.sector_for(routes_by_ticker, ticker, signal),
                **market,
                "gross_margin_acceleration": factors.get("gross_margin_acceleration"),
                "operating_margin_acceleration": factors.get(
                    "operating_margin_acceleration"
                ),
            }
        )

    cells = pd.DataFrame(rows)
    neutral_cols: list[str] = []
    for feature in audit.FEATURES:
        col = f"SN_{feature}"
        neutral_cols.append(col)
        cells[col] = np.nan

    for _, indices in cells.groupby("signal_date").groups.items():
        month = cells.loc[indices].copy()
        for feature in audit.FEATURES:
            cells.loc[indices, f"SN_{feature}"] = audit.sector_neutralize_availability(
                month, feature
            ).to_numpy()

    cells["five_factor_score_eligible"] = cells[neutral_cols].notna().all(axis=1)
    cells["h252_test_cell_eligible"] = (
        cells["five_factor_score_eligible"]
        & cells["H252_LABEL_ENDPOINT"].astype(bool)
    )

    monthly: list[dict[str, object]] = []
    for signal, group in cells.groupby("signal_date", sort=True):
        record = {
            "signal_date": pd.Timestamp(signal).date().isoformat(),
            "members": int(len(group)),
            "exact_signal_price": int(group["exact_signal_price"].sum()),
            "high52": int(group["HIGH_52W_PROXIMITY"].notna().sum()),
            "lowvol63": int(group["LOW_VOL_63D"].notna().sum()),
            "mom_6_1": int(group["MOM_6_1"].notna().sum()),
            "adv63": int(group["ADV63"].notna().sum()),
            "h252_label_endpoint": int(group["H252_LABEL_ENDPOINT"].sum()),
            "gross_margin_acceleration": int(
                group["gross_margin_acceleration"].notna().sum()
            ),
            "operating_margin_acceleration": int(
                group["operating_margin_acceleration"].notna().sum()
            ),
            "five_factor_score_eligible": int(
                group["five_factor_score_eligible"].sum()
            ),
            "h252_test_cells": int(group["h252_test_cell_eligible"].sum()),
        }
        record["acceptance_pass"] = bool(record["h252_test_cells"] >= MIN_ROWS)
        monthly.append(record)

    if len(monthly) != 11:
        raise RuntimeError(f"expected 11 target months, found {len(monthly)}")
    failed = [row for row in monthly if not row["acceptance_pass"]]
    if failed:
        raise RuntimeError(
            "frozen package failed minimum H252 test-cell coverage: "
            + json.dumps(failed, sort_keys=True)
        )
    return cells, monthly


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    membership, frozen_index = load_membership()
    target_tickers = set(membership["ticker"].astype(str))
    official = load_official_lineage()

    direct, direct_failures = direct_fetch(sorted(target_tickers))
    resolved, alias_audit, remaining_failures = resolve_aliases(
        direct,
        direct_failures,
        official,
        target_tickers,
    )
    canonical = canonical_rows(resolved)

    price_path = OUT / "prices_2018-01_2022-08.csv.gz"
    membership_path = OUT / "membership_2020-09_2021-07.csv"
    coverage_path = OUT / "coverage_2020-09_2021-07.csv"
    missing_path = OUT / "missing_tickers.json"
    alias_path = OUT / "alias_audit.json"
    provenance_path = OUT / "provenance.json"
    sums_path = OUT / "SHA256SUMS"

    price_sha = write_deterministic_gzip_csv(canonical, price_path)
    membership.to_csv(
        membership_path,
        index=False,
        lineterminator="\n",
        date_format="%Y-%m-%d",
    )

    cells, monthly = coverage_check(membership, canonical, frozen_index)
    coverage_cols = [
        "signal_date",
        "ticker",
        "exact_signal_price",
        "HIGH_52W_PROXIMITY",
        "LOW_VOL_63D",
        "MOM_6_1",
        "ADV63",
        "H252_LABEL_ENDPOINT",
        "gross_margin_acceleration",
        "operating_margin_acceleration",
        "five_factor_score_eligible",
        "h252_test_cell_eligible",
    ]
    cells[coverage_cols].to_csv(
        coverage_path,
        index=False,
        lineterminator="\n",
        date_format="%Y-%m-%d",
    )
    missing_path.write_text(
        json.dumps(
            {
                "direct_failures": dict(sorted(direct_failures.items())),
                "remaining_unresolved": dict(sorted(remaining_failures.items())),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    alias_path.write_text(
        json.dumps(alias_audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    provenance = {
        "contract": "PRE2021_PRICE_EXTENSION_FREEZE_V1",
        "authority": "FROZEN_RESEARCH_PRICE_EVIDENCE",
        "production_ready": False,
        "performance_metrics_computed": False,
        "fetch_window": {
            "start": FETCH_START,
            "end_exclusive": FETCH_END,
        },
        "target_signal_window": {
            "start_month": START_MONTH,
            "end_month": END_MONTH,
            "months": 11,
        },
        "membership": {
            "rows": int(len(membership)),
            "unique_tickers": int(len(target_tickers)),
            "all_months_exactly_100": bool(
                membership.groupby("signal_date")["ticker"].nunique().eq(100).all()
            ),
        },
        "prices": {
            "rows": int(len(canonical)),
            "canonical_tickers": int(canonical["ticker"].nunique()),
            "direct_tickers": int(
                sum(
                    1
                    for _, group in canonical.groupby("ticker")
                    if group["price_resolution"].iloc[0] == "DIRECT_YAHOO"
                )
            ),
            "alias_tickers": sorted(
                canonical.loc[
                    canonical["price_resolution"].ne("DIRECT_YAHOO"), "ticker"
                ].unique().tolist()
            ),
            "remaining_unresolved_tickers": sorted(remaining_failures),
            "deterministic_gzip_sha256": price_sha,
        },
        "official_lineage": {
            "source_repository": LINEAGE_REPO,
            "source_commit": LINEAGE_COMMIT,
            "path": LINEAGE_PATH,
            "official_workbook_sha256": OFFICIAL_WORKBOOK_SHA256,
            "selected_events": official,
        },
        "monthly_acceptance": monthly,
        "acceptance": {
            "minimum_h252_test_cells_per_month": MIN_ROWS,
            "all_11_target_months_pass": all(
                row["acceptance_pass"] for row in monthly
            ),
        },
        "limitations": [
            "Yahoo/yfinance is vendor-derived research data, not official Borsa daily truth.",
            "Only explicit official Borsa code changes are aliased; merger identities remain unresolved.",
            "Financial and sector inputs used only for coverage acceptance remain the existing frozen experimental sources.",
            "No IC, return, model, portfolio, or champion result is computed."
        ],
    }
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    files = [
        price_path,
        membership_path,
        coverage_path,
        missing_path,
        alias_path,
        provenance_path,
    ]
    sums: list[str] = []
    for path in sorted(files, key=lambda p: p.name):
        sums.append(f"{sha256_bytes(path.read_bytes())}  {path.name}")
    sums_path.write_text("\n".join(sums) + "\n", encoding="utf-8")

    print(json.dumps(provenance, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
