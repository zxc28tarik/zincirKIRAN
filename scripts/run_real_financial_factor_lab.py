#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

SEM_COMMIT = "c8b481e79e270f2c095e8c180671a3f483f0775e"
MARKET_COMMIT = "883e680a2564e38f4c08a21bc88aa95b8f164036"
SEM_BASE = (
    "https://raw.githubusercontent.com/zxc28tarik/TOTAL-RASYO-HESAPLAYICI/"
    f"{SEM_COMMIT}/"
)
MKT_BASE = (
    "https://raw.githubusercontent.com/zxc28tarik/TOTAL-RASYO-HESAPLAYICI/"
    f"{MARKET_COMMIT}/"
)

SEMANTIC_SOURCES = (
    (
        "data/backtest_sources/experimental_semantic_facts_v1/semantic_reports.jsonl.gz",
        "07863ddbd78924ad276e7d0aeba7fa6eec9733477b4ca3c02ece285bcf1d9e7a",
    ),
    (
        "data/backtest_sources/experimental_semantic_facts_v1/semantic_alias_reports.jsonl.gz",
        "adb49330f29b370306d69545db1a48d34a5fda6d763a4d4bdfd2eadc56df06a3",
    ),
    (
        "data/backtest_sources/experimental_semantic_facts_v1/semantic_entity_reports.jsonl.gz",
        "d70e8a1056fd16b03a9ba44c8d6d3c183cb9e2f3604f45692d90817e5b52d741",
    ),
)
MARKET_SOURCES = {
    "prices": (
        "data/backtest_sources/yahoo_resolved/historical_member_prices_resolved_2020-07_2026-08.csv.gz",
        "b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141",
    ),
    "membership": (
        "data/backtest_sources/yahoo_resolved/monthly_member_signal_price_coverage.csv",
        "a3b14014aa4d3ff16a082bc0dac64346b906f4b7720aeae5a8c449a2add314f2",
    ),
    "index": (
        "data/backtest_sources/m3_source_package/index_closes.csv.gz",
        "32a740f7a7114e03c885d1ae75c8bacd081b5254b043521fd76ca5f8e34e786e",
    ),
}

FLOW_FIELDS = (
    "CAPEX",
    "CASH_FLOW_FROM_OPERATIONS",
    "GROSS_PROFIT",
    "NET_INCOME",
    "OPERATING_PROFIT",
    "REVENUE",
)
FACTORS = (
    "accruals",
    "asset_growth",
    "capex_to_assets",
    "cfo_to_assets",
    "gross_margin",
    "gross_margin_acceleration",
    "gross_profitability",
    "operating_margin",
    "operating_margin_acceleration",
    "operating_profitability",
    "roa",
)
LOWER_IS_BETTER = {"accruals", "asset_growth", "capex_to_assets"}
HORIZONS = (20, 60, 120, 252)


def fetch(base: str, path: str, expected: str) -> bytes:
    with urllib.request.urlopen(base + path, timeout=180) as response:
        payload = response.read()
    observed = hashlib.sha256(payload).hexdigest()
    if observed != expected:
        raise RuntimeError(f"hash mismatch {path}: {observed}")
    return payload


def iter_semantic() -> list[dict]:
    rows: list[dict] = []
    for path, digest in SEMANTIC_SOURCES:
        payload = fetch(SEM_BASE, path, digest)
        with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as gz:
            for raw in gz:
                rows.append(json.loads(raw))
    return rows


def csv_from_market(key: str) -> pd.DataFrame:
    path, digest = MARKET_SOURCES[key]
    payload = fetch(MKT_BASE, path, digest)
    if path.endswith(".gz"):
        payload = gzip.decompress(payload)
    return pd.read_csv(io.BytesIO(payload), low_memory=False)


def parse_date(value: object) -> date:
    return pd.Timestamp(value).date()


def quarter_number(day: date) -> int:
    return (day.month - 1) // 3 + 1


def expected_prior_quarter_end(day: date) -> tuple[int, int]:
    q = quarter_number(day)
    if q == 1:
        return day.year - 1, 4
    return day.year, q - 1


def quarter_key(day: date) -> tuple[int, int]:
    return day.year, quarter_number(day)


def latest_fact_map(rows: list[dict], cutoff: date, ticker: str) -> dict[str, list[dict]]:
    selected: dict[tuple[str, date, date], dict] = {}
    for row in rows:
        mapped_ticker = str(row.get("report_mapping_ticker") or "").strip().upper()
        for fact in row.get("facts") or []:
            fact_ticker = str(fact.get("ticker") or "").strip().upper()
            effective_ticker = mapped_ticker or fact_ticker
            if effective_ticker != ticker:
                continue
            if fact.get("sector_family") not in {"NONFIN", "HOLDING"}:
                continue
            published = pd.Timestamp(fact["published_at"])
            if published.date() >= cutoff:
                continue
            field = str(fact.get("canonical_field") or "")
            if field not in set(FLOW_FIELDS) | {"TOTAL_ASSETS"}:
                continue
            start = parse_date(fact["period_start"])
            end = parse_date(fact["period_end"])
            key = (field, start, end)
            prior = selected.get(key)
            if prior is None or pd.Timestamp(prior["published_at"]) < published:
                selected[key] = fact

    by_field: dict[str, list[dict]] = defaultdict(list)
    for (field, _, _), fact in selected.items():
        by_field[field].append(fact)
    for field in by_field:
        by_field[field].sort(key=lambda x: (parse_date(x["period_end"]), parse_date(x["period_start"])))
    return by_field


def numeric(fact: dict) -> float | None:
    try:
        value = float(fact["value"])
    except (TypeError, ValueError, KeyError):
        return None
    return value if math.isfinite(value) else None


def direct_quarters(facts: list[dict]) -> dict[tuple[int, int], float]:
    direct: dict[tuple[int, int], tuple[pd.Timestamp, float]] = {}
    ytd: dict[tuple[int, int], tuple[pd.Timestamp, float]] = {}

    for fact in facts:
        value = numeric(fact)
        if value is None:
            continue
        start = parse_date(fact["period_start"])
        end = parse_date(fact["period_end"])
        days = (end - start).days + 1
        published = pd.Timestamp(fact["published_at"])
        key = quarter_key(end)
        context = str((fact.get("dimensions") or {}).get("context_period_kind") or "").upper()

        if context == "QUARTER" or days <= 100:
            prior = direct.get(key)
            if prior is None or prior[0] < published:
                direct[key] = (published, value)
        elif context == "YTD" or start.month == 1:
            prior = ytd.get(key)
            if prior is None or prior[0] < published:
                ytd[key] = (published, value)

    result = {key: value for key, (_, value) in direct.items()}
    for key, (_, value) in sorted(ytd.items()):
        if key in result:
            continue
        year, q = key
        if q == 1:
            result[key] = value
            continue
        prev_key = (year, q - 1)
        if prev_key in ytd:
            result[key] = value - ytd[prev_key][1]
    return result


def ttm_series(facts: list[dict]) -> dict[tuple[int, int], float]:
    quarters = direct_quarters(facts)
    keys = sorted(quarters)
    result: dict[tuple[int, int], float] = {}
    for i, key in enumerate(keys):
        if i < 3:
            continue
        window = keys[i - 3 : i + 1]
        expected = []
        y, q = key
        for _ in range(4):
            expected.append((y, q))
            if q == 1:
                y -= 1
                q = 4
            else:
                q -= 1
        expected = list(reversed(expected))
        if window == expected:
            result[key] = float(sum(quarters[k] for k in window))
    return result


def latest_assets(facts: list[dict], cutoff: date) -> tuple[date, float] | None:
    candidates: list[tuple[date, pd.Timestamp, float]] = []
    for fact in facts:
        value = numeric(fact)
        if value is None or value <= 0:
            continue
        end = parse_date(fact["period_end"])
        if end >= cutoff:
            continue
        candidates.append((end, pd.Timestamp(fact["published_at"]), value))
    if not candidates:
        return None
    candidates.sort()
    end = candidates[-1][0]
    same = [item for item in candidates if item[0] == end]
    return end, max(same, key=lambda x: x[1])[2]


def assets_year_ago(facts: list[dict], now_end: date) -> float | None:
    target_year = now_end.year - 1
    candidates: list[tuple[int, pd.Timestamp, float]] = []
    for fact in facts:
        value = numeric(fact)
        if value is None or value <= 0:
            continue
        end = parse_date(fact["period_end"])
        if end.year != target_year:
            continue
        distance = abs((end - now_end.replace(year=target_year)).days)
        if distance <= 45:
            candidates.append((distance, pd.Timestamp(fact["published_at"]), value))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], -x[1].timestamp()))
    return candidates[0][2]


def latest_ttm_before(ttm: dict[tuple[int, int], float], period_end: date) -> tuple[tuple[int, int], float] | None:
    keys = [k for k in ttm if k <= quarter_key(period_end)]
    if not keys:
        return None
    key = max(keys)
    return key, ttm[key]


def prior_year_ttm(ttm: dict[tuple[int, int], float], key: tuple[int, int]) -> float | None:
    return ttm.get((key[0] - 1, key[1]))


def _latest_common_ttm(
    ttms: dict[str, dict[tuple[int, int], float]],
    fields: tuple[str, ...],
    max_key: tuple[int, int],
) -> tuple[tuple[int, int], dict[str, float]] | None:
    common = None
    for field in fields:
        keys = {key for key in ttms.get(field, {}) if key <= max_key}
        common = keys if common is None else common.intersection(keys)
    if not common:
        return None
    key = max(common)
    return key, {field: ttms[field][key] for field in fields}


def materialize_financial_factors(by_field: dict[str, list[dict]], cutoff: date) -> dict[str, float]:
    ttms = {field: ttm_series(by_field.get(field, [])) for field in FLOW_FIELDS}
    factors: dict[str, float] = {}

    asset_now = latest_assets(by_field.get("TOTAL_ASSETS", []), cutoff)
    assets_now = None
    assets_prior = None
    avg_assets = None
    asset_end = None
    asset_key = None
    if asset_now is not None:
        asset_end, assets_now = asset_now
        asset_key = quarter_key(asset_end)
        assets_prior = assets_year_ago(by_field.get("TOTAL_ASSETS", []), asset_end)
        if assets_prior is not None and assets_prior > 0:
            avg_assets = (assets_now + assets_prior) / 2.0
            if avg_assets > 0:
                factors["asset_growth"] = assets_now / assets_prior - 1.0

    if asset_key is not None and avg_assets is not None:
        for factor_id, field in (
            ("gross_profitability", "GROSS_PROFIT"),
            ("roa", "NET_INCOME"),
            ("operating_profitability", "OPERATING_PROFIT"),
            ("cfo_to_assets", "CASH_FLOW_FROM_OPERATIONS"),
            ("capex_to_assets", "CAPEX"),
        ):
            item = _latest_common_ttm(ttms, (field,), asset_key)
            if item is not None:
                _, values = item
                factors[factor_id] = values[field] / avg_assets

        accrual_item = _latest_common_ttm(
            ttms,
            ("NET_INCOME", "CASH_FLOW_FROM_OPERATIONS"),
            asset_key,
        )
        if accrual_item is not None:
            _, values = accrual_item
            factors["accruals"] = (
                values["NET_INCOME"] - values["CASH_FLOW_FROM_OPERATIONS"]
            ) / avg_assets

    max_key = asset_key or (cutoff.year, quarter_number(cutoff))

    gross_margin_item = _latest_common_ttm(
        ttms,
        ("GROSS_PROFIT", "REVENUE"),
        max_key,
    )
    if gross_margin_item is not None:
        key, values = gross_margin_item
        revenue = values["REVENUE"]
        if revenue != 0:
            factors["gross_margin"] = values["GROSS_PROFIT"] / revenue
            prior_gross = prior_year_ttm(ttms["GROSS_PROFIT"], key)
            prior_revenue = prior_year_ttm(ttms["REVENUE"], key)
            if prior_gross is not None and prior_revenue not in (None, 0):
                factors["gross_margin_acceleration"] = (
                    values["GROSS_PROFIT"] / revenue
                    - prior_gross / prior_revenue
                )

    operating_margin_item = _latest_common_ttm(
        ttms,
        ("OPERATING_PROFIT", "REVENUE"),
        max_key,
    )
    if operating_margin_item is not None:
        key, values = operating_margin_item
        revenue = values["REVENUE"]
        if revenue != 0:
            factors["operating_margin"] = values["OPERATING_PROFIT"] / revenue
            prior_operating = prior_year_ttm(ttms["OPERATING_PROFIT"], key)
            prior_revenue = prior_year_ttm(ttms["REVENUE"], key)
            if prior_operating is not None and prior_revenue not in (None, 0):
                factors["operating_margin_acceleration"] = (
                    values["OPERATING_PROFIT"] / revenue
                    - prior_operating / prior_revenue
                )

    return {
        key: float(value)
        for key, value in factors.items()
        if math.isfinite(value)
    }


def forward_targets(
    prices: pd.DataFrame,
    index: pd.DataFrame,
    membership: pd.DataFrame,
) -> dict[tuple[date, str], dict[int, float]]:
    prices = prices.copy()
    prices["trade_date"] = pd.to_datetime(prices["trade_date"])
    prices["ticker"] = prices["ticker"].astype(str).str.upper()
    prices["adj_close"] = pd.to_numeric(prices["adj_close"], errors="coerce")
    by_ticker = {
        ticker: frame.sort_values("trade_date").set_index("trade_date")["adj_close"]
        for ticker, frame in prices.groupby("ticker")
    }

    xu = index.loc[index["index_code"].astype(str).eq("XU100")].copy()
    xu["trade_date"] = pd.to_datetime(xu["trade_date"])
    xu["close"] = pd.to_numeric(xu["close"], errors="coerce")
    xu = xu.sort_values("trade_date").dropna(subset=["close"])
    market_dates = xu["trade_date"].tolist()
    market_pos = {day: i for i, day in enumerate(market_dates)}
    market_close = dict(zip(xu["trade_date"], xu["close"], strict=True))

    out: dict[tuple[date, str], dict[int, float]] = {}
    for row in membership.itertuples(index=False):
        signal = pd.Timestamp(row.signal_date)
        ticker = str(row.ticker).upper()
        series = by_ticker.get(ticker)
        if series is None or signal not in series.index or signal not in market_pos:
            continue
        start = float(series.loc[signal])
        if not math.isfinite(start) or start <= 0:
            continue
        vals: dict[int, float] = {}
        for h in HORIZONS:
            pos = market_pos[signal] + h
            if pos >= len(market_dates):
                continue
            future_date = market_dates[pos]
            if future_date not in series.index:
                continue
            end = float(series.loc[future_date])
            m0 = float(market_close[signal])
            m1 = float(market_close[future_date])
            if min(start, end, m0, m1) <= 0:
                continue
            vals[h] = (end / start - 1.0) - (m1 / m0 - 1.0)
        out[(signal.date(), ticker)] = vals
    return out


def metrics(panel: pd.DataFrame, factor: str, horizon: int) -> dict[str, object]:
    target = f"target_{horizon}"
    if factor not in panel.columns or target not in panel.columns:
        return {
            "usable_cells": 0,
            "usable_signal_dates": 0,
            "evaluated_signal_dates": 0,
            "mean_ic": None,
            "ic_std": None,
            "icir": None,
            "mean_top_quintile_excess_return": None,
            "mean_q5_minus_q1": None,
            "mean_monotonicity": None,
            "unavailable_reason": "FACTOR_OR_TARGET_NOT_MATERIALIZED",
        }
    usable = panel[["signal_date", "ticker", factor, target]].dropna().copy()
    ics: list[float] = []
    tops: list[float] = []
    spreads: list[float] = []
    monos: list[float] = []
    for _, group in usable.groupby("signal_date"):
        if len(group) < 20:
            continue
        x = group[factor].astype(float)
        if factor in LOWER_IS_BETTER:
            x = -x
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
        if len(qmeans) == 5:
            mono = pd.Series(qmeans.index.astype(float), index=qmeans.index).corr(qmeans)
            if pd.notna(mono):
                monos.append(float(mono))
    mean_ic = float(np.mean(ics)) if ics else None
    std = float(np.std(ics, ddof=1)) if len(ics) > 1 else None
    return {
        "usable_cells": int(len(usable)),
        "usable_signal_dates": int(usable["signal_date"].nunique()),
        "evaluated_signal_dates": len(ics),
        "mean_ic": mean_ic,
        "ic_std": std,
        "icir": None if mean_ic is None or std in (None, 0) else mean_ic / std,
        "mean_top_quintile_excess_return": float(np.mean(tops)) if tops else None,
        "mean_q5_minus_q1": float(np.mean(spreads)) if spreads else None,
        "mean_monotonicity": float(np.mean(monos)) if monos else None,
    }


def main() -> int:
    semantic = iter_semantic()
    prices = csv_from_market("prices")
    membership = csv_from_market("membership")
    index = csv_from_market("index")
    membership["signal_date"] = pd.to_datetime(membership["signal_date"])
    membership["ticker"] = membership["ticker"].astype(str).str.upper()
    membership = membership[["signal_date", "ticker"]].drop_duplicates()

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

    targets = forward_targets(prices, index, membership)
    panel_rows: list[dict[str, object]] = []
    diagnostics = {
        "membership_cells": int(len(membership)),
        "cells_with_any_semantic_rows": 0,
        "cells_with_materialized_financial_factors": 0,
    }
    for item in membership.itertuples(index=False):
        signal = pd.Timestamp(item.signal_date).date()
        ticker = str(item.ticker).upper()
        fact_rows = rows_by_ticker.get(ticker)
        if not fact_rows:
            continue
        diagnostics["cells_with_any_semantic_rows"] += 1
        by_field = latest_fact_map(fact_rows, signal, ticker)
        factors = materialize_financial_factors(by_field, signal)
        if not factors:
            continue
        diagnostics["cells_with_materialized_financial_factors"] += 1
        row: dict[str, object] = {"signal_date": signal, "ticker": ticker}
        row.update(factors)
        for h, value in targets.get((signal, ticker), {}).items():
            row[f"target_{h}"] = value
        panel_rows.append(row)

    panel = pd.DataFrame(panel_rows)
    if panel.empty:
        raise RuntimeError(
            "financial factor panel is empty; diagnostics="
            + json.dumps(diagnostics, sort_keys=True)
        )
    results = {
        factor: {str(h): metrics(panel, factor, h) for h in HORIZONS}
        for factor in FACTORS
    }
    receipt = {
        "contract": "FIRST_REAL_FINANCIAL_FACTOR_LAB_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "semantic_source_commit": SEM_COMMIT,
        "market_source_commit": MARKET_COMMIT,
        "semantic_reports": 5052,
        "semantic_facts": 199969,
        "historical_membership_cells": int(len(membership)),
        "materialized_financial_factor_cells": int(len(panel)),
        "materialized_signal_dates": int(panel["signal_date"].nunique()),
        "diagnostics": {
            **diagnostics,
            "materialized_factor_columns": sorted(
                factor for factor in FACTORS if factor in panel.columns
            ),
            "factor_nonnull_counts": {
                factor: int(panel[factor].notna().sum()) if factor in panel.columns else 0
                for factor in FACTORS
            },
        },
        "factors": FACTORS,
        "horizons": HORIZONS,
        "results": results,
        "limitations": [
            "Semantic corpus remains EXPERIMENTAL_VERSION_RISK because historical superseded-version enumeration is incomplete.",
            "Financial factors are restricted to NONFIN/HOLDING semantic facts.",
            "Forward returns use Yahoo adjusted-close minus XU100 as a diagnostic return proxy.",
            "No factor weighting, threshold tuning, or production promotion is authorized.",
        ],
    }
    out = Path("research/evidence_runs/first_real_financial_factor_lab_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
