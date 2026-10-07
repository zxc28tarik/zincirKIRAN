#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
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
import run_first_equal_weight_multifactor_challenger as ew  # noqa: E402
import run_real_financial_factor_lab as fin  # noqa: E402
import run_real_sector_neutral_decorrelation as sn  # noqa: E402
import run_real_walk_forward_factor_stability as wf  # noqa: E402

START_MONTH = "2019-04"
END_MONTH = "2021-07"
STOCK_START = "2018-01-01"
STOCK_END = "2022-09-01"
CALENDAR_START = "2018-01-01"
CALENDAR_END = "2026-09-01"
MIN_ROWS = 20
FEATURES = (
    "HIGH_52W_PROXIMITY",
    "LOW_VOL_63D",
    "MOM_6_1",
    "operating_margin_acceleration",
    "gross_margin_acceleration",
)
KNOWN_LINEAGE_CANDIDATES = {
    "GUSGR": {
        "successor": "TURSG",
        "effective_date": "2020-09-02",
        "use_in_eligibility": False,
        "reason": "42A explicit lineage event; candidate is reported but not auto-aliased in this coverage audit."
    }
}


def _normalize_history(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(
            columns=["trade_date", "open", "high", "low", "close", "adj_close", "volume"]
        )
    out = frame.copy().reset_index()
    date_col = "Date" if "Date" in out.columns else out.columns[0]
    out["trade_date"] = pd.to_datetime(out[date_col], errors="coerce").dt.tz_localize(None).dt.normalize()
    mapping = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    }
    for source, target in mapping.items():
        if source in out.columns:
            out[target] = pd.to_numeric(out[source], errors="coerce")
        else:
            out[target] = np.nan
    if out["adj_close"].isna().all():
        out["adj_close"] = out["close"]
    out = out[
        ["trade_date", "open", "high", "low", "close", "adj_close", "volume"]
    ].dropna(subset=["trade_date"]).sort_values("trade_date")
    out = out.drop_duplicates("trade_date", keep="last").reset_index(drop=True)
    return out


def _fetch_symbol(symbol: str, start: str, end: str, attempts: int = 4) -> tuple[pd.DataFrame, str | None]:
    last: str | None = None
    for attempt in range(attempts):
        try:
            frame = yf.Ticker(symbol).history(
                start=start,
                end=end,
                auto_adjust=False,
                actions=False,
                repair=False,
                raise_errors=True,
            )
            normalized = _normalize_history(frame)
            if normalized.empty:
                last = "EMPTY"
            else:
                return normalized, None
        except Exception as exc:  # network/vendor discovery audit
            last = repr(exc)
        time.sleep(0.8 * (attempt + 1))
    return _normalize_history(pd.DataFrame()), last


def fetch_histories(tickers: list[str]) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    histories: dict[str, pd.DataFrame] = {}
    failures: dict[str, str] = {}

    def one(ticker: str) -> tuple[str, pd.DataFrame, str | None]:
        frame, err = _fetch_symbol(f"{ticker}.IS", STOCK_START, STOCK_END)
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


def fetch_index_calendar() -> pd.DataFrame:
    frame, err = _fetch_symbol("XU100.IS", CALENDAR_START, CALENDAR_END)
    if frame.empty:
        raise RuntimeError(f"XU100.IS calendar fetch failed: {err}")
    usable = frame.loc[
        frame["close"].notna() & (frame["close"] > 0),
        ["trade_date", "close"],
    ].copy()
    if usable.empty:
        raise RuntimeError("XU100.IS returned no positive closes")
    return usable.sort_values("trade_date").reset_index(drop=True)


def load_frozen_index_calendar() -> pd.DataFrame:
    frame = fin.csv_from_market("index")
    xu = frame.loc[frame["index_code"].astype(str).eq("XU100")].copy()
    xu["trade_date"] = pd.to_datetime(xu["trade_date"], errors="raise").dt.normalize()
    xu["close"] = pd.to_numeric(xu["close"], errors="coerce")
    xu = xu.loc[xu["close"].notna() & (xu["close"] > 0), ["trade_date", "close"]]
    xu = xu.sort_values("trade_date").drop_duplicates("trade_date").reset_index(drop=True)
    if xu.empty:
        raise RuntimeError("frozen XU100 calendar is empty")
    return xu


def build_hybrid_calendar(
    live_calendar: pd.DataFrame,
    frozen_calendar: pd.DataFrame,
) -> pd.DataFrame:
    frozen_start = pd.Timestamp(frozen_calendar["trade_date"].min())
    early = live_calendar.loc[
        live_calendar["trade_date"] < frozen_start,
        ["trade_date", "close"],
    ].copy()
    combined = pd.concat([early, frozen_calendar], ignore_index=True)
    combined = (
        combined.sort_values("trade_date")
        .drop_duplicates("trade_date", keep="last")
        .reset_index(drop=True)
    )
    return combined


def load_membership_events() -> tuple[set[str], list[dict[str, object]]]:
    catalog = json.loads(backcast.CATALOG_PATH.read_text(encoding="utf-8"))
    anchor, _ = backcast.load_anchor(catalog)
    events = backcast.all_events(catalog)
    state = set(anchor)
    for event in reversed(events):
        state = backcast.reverse_event(state, event)
    if len(state) != 100:
        raise RuntimeError("earliest reconstructed membership must contain 100 names")
    return state, events


def monthly_signal_dates(index_calendar: pd.DataFrame) -> list[pd.Timestamp]:
    months = pd.period_range(START_MONTH, END_MONTH, freq="M")
    frame = index_calendar.copy()
    frame["month"] = frame["trade_date"].dt.to_period("M")
    out: list[pd.Timestamp] = []
    for month in months:
        rows = frame.loc[frame["month"] == month].sort_values("trade_date")
        if rows.empty:
            raise RuntimeError(f"XU100 calendar has no trading day for {month}")
        out.append(pd.Timestamp(rows.iloc[0]["trade_date"]))
    return out


def monthly_membership(
    earliest_state: set[str],
    events: list[dict[str, object]],
    signal_dates: list[pd.Timestamp],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for signal in signal_dates:
        state = set(earliest_state)
        for event in events:
            if pd.Timestamp(event["effective_date"]) <= signal:
                state = backcast.forward_event(state, event)
        if len(state) != 100:
            raise RuntimeError(f"membership count !=100 on {signal.date()}: {len(state)}")
        for ticker in sorted(state):
            rows.append({"signal_date": signal, "ticker": ticker})
    return pd.DataFrame(rows)


def factor_market_values(
    history: pd.DataFrame,
    signal: pd.Timestamp,
    market_dates: list[pd.Timestamp],
    market_pos: dict[pd.Timestamp, int],
) -> dict[str, object]:
    if history.empty:
        return {
            "exact_signal_price": False,
            "HIGH_52W_PROXIMITY": None,
            "LOW_VOL_63D": None,
            "MOM_6_1": None,
            "ADV63": None,
            "H252_LABEL_ENDPOINT": False,
        }

    positions = {
        pd.Timestamp(day): idx
        for idx, day in enumerate(history["trade_date"])
    }
    pos = positions.get(signal)
    if pos is None:
        return {
            "exact_signal_price": False,
            "HIGH_52W_PROXIMITY": None,
            "LOW_VOL_63D": None,
            "MOM_6_1": None,
            "ADV63": None,
            "H252_LABEL_ENDPOINT": False,
        }

    adj = history["adj_close"].to_numpy(dtype=float)
    close = history["close"].to_numpy(dtype=float)
    volume = history["volume"].to_numpy(dtype=float)

    high52 = None
    if pos >= 251:
        window = adj[pos - 251 : pos + 1]
        if len(window) == 252 and np.all(np.isfinite(window)) and np.all(window > 0):
            high = float(np.max(window))
            if high > 0:
                high52 = float(adj[pos] / high)

    lowvol = None
    if pos >= 63:
        window = adj[pos - 63 : pos + 1]
        if len(window) == 64 and np.all(np.isfinite(window)) and np.all(window > 0):
            returns = window[1:] / window[:-1] - 1.0
            lowvol = -float(np.std(returns, ddof=1))

    mom61 = None
    if (
        pos >= 126
        and math.isfinite(adj[pos - 21])
        and math.isfinite(adj[pos - 126])
        and adj[pos - 21] > 0
        and adj[pos - 126] > 0
    ):
        mom61 = float(adj[pos - 21] / adj[pos - 126] - 1.0)

    adv63 = None
    if pos >= 62:
        px = close[pos - 62 : pos + 1]
        vol = volume[pos - 62 : pos + 1]
        mask = np.isfinite(px) & np.isfinite(vol) & (px > 0) & (vol >= 0)
        if int(mask.sum()) == 63:
            adv63 = float(np.mean(px[mask] * vol[mask]))

    label_endpoint = False
    mpos = market_pos.get(signal)
    if mpos is not None and mpos + 252 < len(market_dates):
        future = market_dates[mpos + 252]
        fpos = positions.get(future)
        if fpos is not None:
            value = adj[fpos]
            label_endpoint = bool(math.isfinite(value) and value > 0)

    return {
        "exact_signal_price": bool(
            math.isfinite(float(adj[pos])) and float(adj[pos]) > 0
        ),
        "HIGH_52W_PROXIMITY": high52,
        "LOW_VOL_63D": lowvol,
        "MOM_6_1": mom61,
        "ADV63": adv63,
        "H252_LABEL_ENDPOINT": label_endpoint,
    }


def build_financial_index() -> dict[str, list[dict]]:
    semantic = fin.iter_semantic()
    rows_by_ticker: dict[str, list[dict]] = defaultdict(list)
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
                rows_by_ticker[ticker].append(row)
    return rows_by_ticker


def sector_neutralize_availability(
    month: pd.DataFrame,
    feature: str,
) -> pd.Series:
    out = pd.Series(np.nan, index=month.index, dtype=float)
    usable = month.loc[
        month[feature].notna() & month["sector"].notna(),
        ["sector", feature],
    ]
    for _, group in usable.groupby("sector", sort=True):
        if len(group) < sn.MIN_SECTOR_SIZE:
            continue
        out.loc[group.index] = group[feature].astype(float).rank(
            method="average", pct=True
        ) - 0.5
    return out


def expected_evaluable_blocks(
    signal_dates: list[pd.Timestamp],
    evaluable_dates: set[pd.Timestamp],
    calendar: pd.DataFrame,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ordered = sorted(pd.Timestamp(x) for x in signal_dates)
    maturity = wf.maturity_map(ordered, calendar, 252)
    calendar_blocks = wf.validation_blocks(ordered, maturity)

    raw_rows: list[dict[str, object]] = []
    evaluated_rows: list[dict[str, object]] = []
    for idx, block in enumerate(calendar_blocks, start=1):
        test_start = min(block)
        test_end = max(block)
        train_dates = [
            signal
            for signal in ordered
            if signal < test_start
            and maturity.get(signal) is not None
            and maturity[signal] < test_start
        ]
        valid_test_dates = [
            signal for signal in block if pd.Timestamp(signal) in evaluable_dates
        ]
        row = {
            "fold_index": idx,
            "validation_start": test_start.date().isoformat(),
            "validation_end": test_end.date().isoformat(),
            "calendar_signal_months": len(block),
            "evaluable_signal_months": len(valid_test_dates),
            "evaluable_signal_dates": [
                day.date().isoformat() for day in valid_test_dates
            ],
            "train_signal_months": len(train_dates),
            "validation_last_label_maturity": (
                None
                if maturity.get(test_end) is None
                else maturity[test_end].date().isoformat()
            ),
        }
        raw_rows.append(row)
        if len(train_dates) < wf.MIN_INITIAL_TRAIN_MONTHS:
            continue
        if len(valid_test_dates) < wf.MIN_TEST_MONTHS:
            continue
        if maturity.get(test_end) is None:
            continue
        evaluated_rows.append(row)
    return raw_rows, evaluated_rows


def main() -> int:
    live_index_calendar = fetch_index_calendar()
    frozen_index_calendar = load_frozen_index_calendar()
    index_calendar = build_hybrid_calendar(
        live_index_calendar,
        frozen_index_calendar,
    )
    signal_dates = monthly_signal_dates(index_calendar)
    earliest_state, events = load_membership_events()
    membership = monthly_membership(earliest_state, events, signal_dates)

    unique_tickers = sorted(membership["ticker"].unique())
    histories, failures = fetch_histories(unique_tickers)

    market_dates = [
        pd.Timestamp(day) for day in index_calendar["trade_date"].tolist()
    ]
    market_pos = {day: idx for idx, day in enumerate(market_dates)}

    financial_index = build_financial_index()
    routes = sn.load_sector_routes()
    routes_by_ticker = {
        ticker: group.copy()
        for ticker, group in routes.groupby("ticker", sort=False)
    }

    cell_rows: list[dict[str, object]] = []
    for item in membership.itertuples(index=False):
        signal = pd.Timestamp(item.signal_date)
        ticker = str(item.ticker)
        market = factor_market_values(
            histories.get(ticker, pd.DataFrame()),
            signal,
            market_dates,
            market_pos,
        )

        factors: dict[str, float] = {}
        fact_rows = financial_index.get(ticker)
        if fact_rows:
            by_field = fin.latest_fact_map(fact_rows, signal.date(), ticker)
            factors = fin.materialize_financial_factors(by_field, signal.date())

        cell_rows.append(
            {
                "signal_date": signal,
                "ticker": ticker,
                "sector": sn.sector_for(routes_by_ticker, ticker, signal),
                **market,
                "gross_margin_acceleration": factors.get(
                    "gross_margin_acceleration"
                ),
                "operating_margin_acceleration": factors.get(
                    "operating_margin_acceleration"
                ),
            }
        )

    cells = pd.DataFrame(cell_rows)

    neutral_cols: list[str] = []
    for feature in FEATURES:
        col = f"SN_{feature}"
        neutral_cols.append(col)
        cells[col] = np.nan

    for signal, indices in cells.groupby("signal_date").groups.items():
        month = cells.loc[indices].copy()
        for feature in FEATURES:
            cells.loc[indices, f"SN_{feature}"] = sector_neutralize_availability(
                month,
                feature,
            ).to_numpy()

    cells["FIVE_FACTOR_SCORE_ELIGIBLE"] = cells[neutral_cols].notna().all(axis=1)
    cells["H252_TEST_CELL_ELIGIBLE"] = (
        cells["FIVE_FACTOR_SCORE_ELIGIBLE"]
        & cells["H252_LABEL_ENDPOINT"].astype(bool)
    )

    monthly: list[dict[str, object]] = []
    eligible_pre_dates: list[pd.Timestamp] = []
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
            "sector_route": int(group["sector"].notna().sum()),
            "gross_margin_acceleration": int(
                group["gross_margin_acceleration"].notna().sum()
            ),
            "operating_margin_acceleration": int(
                group["operating_margin_acceleration"].notna().sum()
            ),
            "five_factor_score_eligible": int(
                group["FIVE_FACTOR_SCORE_ELIGIBLE"].sum()
            ),
            "h252_test_cells": int(group["H252_TEST_CELL_ELIGIBLE"].sum()),
            "h252_test_month_eligible": bool(
                int(group["H252_TEST_CELL_ELIGIBLE"].sum()) >= MIN_ROWS
            ),
        }
        monthly.append(record)
        if record["h252_test_month_eligible"]:
            eligible_pre_dates.append(pd.Timestamp(signal))

    # Frozen original 60-month signal dates are used only for the power baseline.
    anchor_catalog = json.loads(backcast.CATALOG_PATH.read_text(encoding="utf-8"))
    _, anchor_meta = backcast.load_anchor(anchor_catalog)
    import urllib.request
    with urllib.request.urlopen(anchor_meta["url"], timeout=120) as response:
        anchor_payload = response.read()
    anchor_sha = hashlib.sha256(anchor_payload).hexdigest()
    if anchor_sha != anchor_meta["sha256"]:
        raise RuntimeError("original membership anchor changed during power audit")
    original = pd.read_csv(
        pd.io.common.BytesIO(anchor_payload),
        usecols=["signal_date"],
    )
    original_dates = sorted(
        pd.Timestamp(x)
        for x in pd.to_datetime(original["signal_date"]).dropna().unique()
    )
    if len(original_dates) != 60:
        raise RuntimeError(f"expected 60 original signal dates, found {len(original_dates)}")

    frozen_common_panel, _ = ew.build_common_panel()
    frozen_common_panel["signal_date"] = pd.to_datetime(
        frozen_common_panel["signal_date"]
    ).dt.normalize()
    original_signal_dates = sorted(
        pd.Timestamp(x)
        for x in frozen_common_panel["signal_date"].dropna().unique()
    )
    if original_signal_dates != original_dates:
        raise RuntimeError(
            "frozen common-panel signal dates do not match pinned 60-month anchor"
        )

    original_evaluable_dates = {
        pd.Timestamp(signal)
        for signal, group in frozen_common_panel.groupby("signal_date")
        if int(group["TARGET_252"].notna().sum()) >= MIN_ROWS
    }
    current_calendar_blocks, current_blocks = expected_evaluable_blocks(
        original_dates,
        original_evaluable_dates,
        frozen_index_calendar,
    )
    if len(current_blocks) != 1:
        raise RuntimeError(
            "frozen common-panel H252 sanity mismatch: "
            f"expected 1 existing evaluable fold from Implementation 35, found {len(current_blocks)}"
        )

    eligible_pre_score_dates = {
        pd.Timestamp(row["signal_date"])
        for row in monthly
        if int(row["five_factor_score_eligible"]) >= MIN_ROWS
    }
    pre_evaluable_dates = {
        pd.Timestamp(row["signal_date"])
        for row in monthly
        if bool(row["h252_test_month_eligible"])
    }
    extended_dates = sorted(set(original_dates) | eligible_pre_score_dates)
    extended_evaluable_dates = original_evaluable_dates | pre_evaluable_dates
    extended_calendar_blocks, extended_blocks = expected_evaluable_blocks(
        extended_dates,
        extended_evaluable_dates,
        index_calendar,
    )

    lineage_candidates: dict[str, object] = {}
    for old, meta in KNOWN_LINEAGE_CANDIDATES.items():
        successor = str(meta["successor"])
        successor_frame, successor_err = _fetch_symbol(
            f"{successor}.IS", STOCK_START, STOCK_END
        )
        effective = pd.Timestamp(meta["effective_date"])
        pre_rows = int(
            (successor_frame["trade_date"] < effective).sum()
        ) if not successor_frame.empty else 0
        lineage_candidates[old] = {
            **meta,
            "direct_old_symbol_available": old in histories,
            "successor_symbol_available": not successor_frame.empty,
            "successor_pre_effective_rows": pre_rows,
            "successor_fetch_error": successor_err,
        }

    earliest_score = next(
        (
            row["signal_date"]
            for row in monthly
            if row["five_factor_score_eligible"] >= MIN_ROWS
        ),
        None,
    )
    earliest_h252 = next(
        (
            row["signal_date"]
            for row in monthly
            if row["h252_test_month_eligible"]
        ),
        None,
    )

    receipt = {
        "contract": "PRE2021_COVERAGE_POWER_AUDIT_V1",
        "authority": "COVERAGE_AUDIT_ONLY",
        "production_ready": False,
        "performance_metrics_computed": False,
        "model_fit_performed": False,
        "runtime": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "yfinance": importlib.metadata.version("yfinance"),
        },
        "membership": {
            "start_month": START_MONTH,
            "end_month": END_MONTH,
            "signal_months": len(signal_dates),
            "cells": int(len(membership)),
            "unique_tickers": int(len(unique_tickers)),
            "all_months_exactly_100": bool(
                all(item["members"] == 100 for item in monthly)
            ),
        },
        "price_discovery": {
            "start": STOCK_START,
            "end_exclusive": STOCK_END,
            "direct_tickers_requested": int(len(unique_tickers)),
            "direct_tickers_with_nonempty_history": int(len(histories)),
            "direct_tickers_empty_or_failed": int(len(failures)),
            "empty_or_failed": dict(sorted(failures.items())),
            "known_lineage_candidates": lineage_candidates,
            "alias_policy": "REPORT_ONLY_NOT_USED_FOR_ELIGIBILITY",
        },
        "financial_source": {
            "semantic_commit": fin.SEM_COMMIT,
            "semantic_sources": [
                {"path": path, "sha256": digest}
                for path, digest in fin.SEMANTIC_SOURCES
            ],
            "authority": "EXPERIMENTAL_VERSION_RISK",
        },
        "sector_source": {
            "commit": sn.SOURCE_COMMIT,
            "path": sn.SECTOR_PATH,
            "sha256": sn.SECTOR_SHA256,
            "minimum_sector_size": sn.MIN_SECTOR_SIZE,
        },
        "monthly_coverage": monthly,
        "mechanical_eligibility": {
            "minimum_rows_per_test_month": MIN_ROWS,
            "earliest_five_factor_score_month": earliest_score,
            "earliest_h252_test_month": earliest_h252,
            "eligible_pre2021_signal_dates": [
                day.date().isoformat() for day in eligible_pre_dates
            ],
        },
        "calendar_evidence": {
            "live_yahoo_discovery": {
                "symbol": "XU100.IS",
                "start": CALENDAR_START,
                "end_exclusive": CALENDAR_END,
                "min_trade_date": live_index_calendar["trade_date"].min().date().isoformat(),
                "max_trade_date": live_index_calendar["trade_date"].max().date().isoformat(),
                "role": "DISCOVERY_ONLY_FOR_DATES_BEFORE_FROZEN_CALENDAR_START"
            },
            "frozen_existing": {
                "source_commit": fin.MARKET_COMMIT,
                "path": fin.MARKET_SOURCES["index"][0],
                "sha256": fin.MARKET_SOURCES["index"][1],
                "min_trade_date": frozen_index_calendar["trade_date"].min().date().isoformat(),
                "max_trade_date": frozen_index_calendar["trade_date"].max().date().isoformat(),
                "role": "AUTHORITATIVE_EXISTING_RESEARCH_CALENDAR"
            },
            "hybrid_rule": "LIVE_ONLY_BEFORE_FROZEN_MIN_DATE_THEN_FROZEN",
        },
        "h252_power": {
            "sanity_rule": "CURRENT_FROZEN_COMMON_PANEL_MUST_REPRODUCE_IMPLEMENTATION35_ONE_EVALUABLE_H252_FOLD",
            "sanity_pass": len(current_blocks) == 1,
            "minimum_evaluable_months_per_fold": wf.MIN_TEST_MONTHS,
            "minimum_rows_per_evaluable_month": MIN_ROWS,
            "current_original_signal_dates": len(original_dates),
            "current_h252_evaluable_signal_dates": len(original_evaluable_dates),
            "current_calendar_blocks": current_calendar_blocks,
            "current_evaluable_blocks": current_blocks,
            "current_expected_fold_count": len(current_blocks),
            "extended_signal_dates": len(extended_dates),
            "extended_h252_evaluable_signal_dates": len(extended_evaluable_dates),
            "extended_calendar_blocks": extended_calendar_blocks,
            "extended_evaluable_blocks": extended_blocks,
            "extended_expected_fold_count": len(extended_blocks),
            "additional_expected_folds": len(extended_blocks) - len(current_blocks),
        },
        "limitations": [
            "Yahoo/yfinance discovery is live vendor availability evidence and is not frozen price authority.",
            "A protocol-amendment sanity correction uses the frozen existing XU100 calendar for the current baseline and live Yahoo dates only before the frozen calendar starts; this correction was made because the original live-calendar baseline failed to reproduce Implementation 35's known one-fold H252 mechanics.",
            "Direct historical ticker codes are used for eligibility; lineage candidates are reported but not auto-applied.",
            "The financial corpus remains EXPERIMENTAL_VERSION_RISK and is not extended by this audit.",
            "This audit measures data/test mechanics only and computes no alpha performance.",
            "A later acquisition implementation must freeze and hash any price history before factor/model reruns."
        ],
    }

    out = ROOT / "research/evidence_runs/pre2021_coverage_power_audit_v1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
