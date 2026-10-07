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

import run_first_equal_weight_multifactor_challenger as ew  # noqa: E402
import run_long_only_cost_sensitivity as cost  # noqa: E402
import run_nested_train_only_evidence_weighted_composite as dyn  # noqa: E402
import run_real_price_factor_lab as price  # noqa: E402
import run_real_walk_forward_factor_stability as wf  # noqa: E402

CHAMPION = ew.CHAMPION
EW5 = ew.COMPOSITE
DYNAMIC = dyn.DYNAMIC
CONTENDERS = (CHAMPION, EW5, DYNAMIC)
HORIZONS = ew.HORIZONS
PARTICIPATION_RATES = (0.01, 0.05, 0.10)
EXECUTION_DAYS = (1, 3)
NOTIONALS_TRY = (1_000_000, 5_000_000, 10_000_000, 25_000_000, 50_000_000)
TOP_FRACTION = cost.TOP_FRACTION
MIN_CROSS_SECTION = cost.MIN_CROSS_SECTION


def load_adv63() -> tuple[dict[tuple[pd.Timestamp, str], float], dict[str, object]]:
    meta = price.SOURCES["daily_prices"]
    payload = price.fetch_verified(meta["path"], meta["sha256"])
    daily = price._clean_daily(price.read_csv_payload(payload, gzipped=True))
    daily["traded_notional"] = (
        daily["close"].astype(float) * daily["volume"].astype(float)
    )

    adv_map: dict[tuple[pd.Timestamp, str], float] = {}
    usable_rows = 0
    for ticker, group in daily.groupby("ticker", sort=False):
        work = group[["trade_date", "traded_notional"]].copy()
        vals = work["traded_notional"].astype(float)
        rolling = vals.rolling(window=63, min_periods=63).mean()
        for trade_date, adv in zip(work["trade_date"], rolling, strict=True):
            if pd.notna(adv) and math.isfinite(float(adv)) and float(adv) > 0:
                adv_map[(pd.Timestamp(trade_date), str(ticker))] = float(adv)
                usable_rows += 1

    source = {
        "source_commit": price.TOTAL_RASYO_COMMIT,
        "path": meta["path"],
        "sha256": meta["sha256"],
        "daily_rows": int(len(daily)),
        "adv63_rows": int(usable_rows),
        "authority": "VALIDATED_DERIVED_MARKET_DATA",
    }
    return adv_map, source


def _portfolio_weights(
    group: pd.DataFrame,
    score: pd.Series,
    target_col: str,
) -> dict[str, float] | None:
    work = group[["ticker", target_col]].copy()
    work["score"] = score
    work = work.dropna(subset=["ticker", target_col, "score"])
    if len(work) < MIN_CROSS_SECTION:
        return None

    selected_count = max(1, int(math.ceil(len(work) * TOP_FRACTION)))
    selected = (
        work.sort_values(["score", "ticker"], ascending=[False, True])
        .head(selected_count)
        .copy()
    )
    weight = 1.0 / selected_count
    return {
        str(ticker): weight
        for ticker in selected["ticker"].astype(str)
    }


def _scenario_key(participation: float, days: int) -> str:
    return f"p{int(round(participation * 100))}_d{days}"


def _capacity_row(
    *,
    signal_date: pd.Timestamp,
    previous: dict[str, float],
    current: dict[str, float],
    adv_map: dict[tuple[pd.Timestamp, str], float],
) -> dict[str, object]:
    names = sorted(set(previous) | set(current))
    legs: list[dict[str, object]] = []
    missing: list[str] = []
    gross_turnover = 0.0

    for ticker in names:
        delta = float(current.get(ticker, 0.0) - previous.get(ticker, 0.0))
        absolute_delta = abs(delta)
        if absolute_delta <= 1e-15:
            continue
        gross_turnover += absolute_delta
        adv = adv_map.get((pd.Timestamp(signal_date), ticker))
        if adv is None:
            missing.append(ticker)
            continue
        legs.append(
            {
                "ticker": ticker,
                "delta_weight": delta,
                "absolute_delta_weight": absolute_delta,
                "adv63_try": adv,
            }
        )

    selected_advs = [
        adv_map.get((pd.Timestamp(signal_date), ticker))
        for ticker in current
    ]
    selected_valid = [
        float(value) for value in selected_advs
        if value is not None and math.isfinite(float(value)) and float(value) > 0
    ]

    row: dict[str, object] = {
        "signal_date": pd.Timestamp(signal_date).date().isoformat(),
        "gross_turnover": float(gross_turnover),
        "trade_legs": int(len(legs) + len(missing)),
        "missing_adv_tickers": missing,
        "selected_names": int(len(current)),
        "selected_adv_coverage": (
            0.0 if not current else len(selected_valid) / len(current)
        ),
        "selected_min_adv63_try": (
            None if not selected_valid else float(min(selected_valid))
        ),
        "selected_median_adv63_try": (
            None if not selected_valid else float(np.median(selected_valid))
        ),
        "capacity": {},
    }

    if gross_turnover <= 1e-15:
        row["status"] = "NO_TRADE_NO_CAPACITY_BINDING"
        return row

    if missing:
        row["status"] = "CAPACITY_UNAVAILABLE_MISSING_ADV"
        return row

    if not legs:
        row["status"] = "CAPACITY_UNAVAILABLE_NO_VALID_LEGS"
        return row

    capacity: dict[str, float] = {}
    for participation in PARTICIPATION_RATES:
        for days in EXECUTION_DAYS:
            key = _scenario_key(participation, days)
            limits = [
                float(leg["adv63_try"])
                * participation
                * days
                / float(leg["absolute_delta_weight"])
                for leg in legs
            ]
            capacity[key] = float(min(limits))
    row["capacity"] = capacity
    row["status"] = "CAPACITY_EVALUATED"
    return row


def _summarize_capacity(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {
            "signal_dates": 0,
            "capacity_evaluated_dates": 0,
            "missing_adv_dates": 0,
            "no_trade_dates": 0,
            "mean_gross_turnover": None,
            "selected_adv": {},
            "scenarios": {},
        }

    turnover = np.array([float(row["gross_turnover"]) for row in rows], dtype=float)
    evaluated = [row for row in rows if row["status"] == "CAPACITY_EVALUATED"]
    missing = [row for row in rows if row["status"] == "CAPACITY_UNAVAILABLE_MISSING_ADV"]
    no_trade = [row for row in rows if row["status"] == "NO_TRADE_NO_CAPACITY_BINDING"]

    selected_min = [
        float(row["selected_min_adv63_try"])
        for row in rows
        if row["selected_min_adv63_try"] is not None
    ]
    selected_median = [
        float(row["selected_median_adv63_try"])
        for row in rows
        if row["selected_median_adv63_try"] is not None
    ]
    selected_coverage = [
        float(row["selected_adv_coverage"]) for row in rows
    ]

    scenarios: dict[str, object] = {}
    for participation in PARTICIPATION_RATES:
        for days in EXECUTION_DAYS:
            key = _scenario_key(participation, days)
            values = np.array(
                [float(row["capacity"][key]) for row in evaluated],
                dtype=float,
            )
            support: dict[str, float] = {}
            total_dates = len(rows)
            for notional in NOTIONALS_TRY:
                supported = sum(
                    1
                    for row in evaluated
                    if float(row["capacity"][key]) >= notional
                ) + len(no_trade)
                support[str(notional)] = (
                    0.0 if total_dates == 0 else supported / total_dates
                )

            scenarios[key] = {
                "participation_rate": participation,
                "execution_days": days,
                "evaluated_trade_dates": int(len(values)),
                "worst_capacity_try": (
                    None if len(values) == 0 else float(np.min(values))
                ),
                "p10_capacity_try": (
                    None if len(values) == 0 else float(np.quantile(values, 0.10))
                ),
                "median_capacity_try": (
                    None if len(values) == 0 else float(np.median(values))
                ),
                "mean_capacity_try": (
                    None if len(values) == 0 else float(np.mean(values))
                ),
                "support_fraction_by_portfolio_notional_try": support,
            }

    return {
        "signal_dates": int(len(rows)),
        "capacity_evaluated_dates": int(len(evaluated)),
        "missing_adv_dates": int(len(missing)),
        "no_trade_dates": int(len(no_trade)),
        "mean_gross_turnover": float(turnover.mean()),
        "selected_adv": {
            "mean_selected_adv_coverage": float(np.mean(selected_coverage)),
            "worst_selected_adv_coverage": float(np.min(selected_coverage)),
            "mean_selected_min_adv63_try": (
                None if not selected_min else float(np.mean(selected_min))
            ),
            "median_selected_min_adv63_try": (
                None if not selected_min else float(np.median(selected_min))
            ),
            "mean_selected_median_adv63_try": (
                None if not selected_median else float(np.mean(selected_median))
            ),
        },
        "scenarios": scenarios,
    }


def run_horizon(
    panel: pd.DataFrame,
    calendar: pd.DataFrame,
    adv_map: dict[tuple[pd.Timestamp, str], float],
    horizon: int,
) -> dict[str, object]:
    target = f"TARGET_{horizon}"
    signal_dates = sorted(
        pd.Timestamp(x) for x in panel["signal_date"].dropna().unique()
    )
    maturity = wf.maturity_map(signal_dates, calendar, horizon)
    blocks = wf.validation_blocks(signal_dates, maturity)

    fold_records: list[dict[str, object]] = []
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

        evidence = dyn._factor_train_evidence(panel, horizon, train_dates)
        dynamic_weights = dyn._weights(evidence)
        if dynamic_weights is None:
            fold_records.append(
                {
                    "fold_id": f"H{horizon}-F{idx}",
                    "status": "NO_SIGNAL_ZERO_POSITIVE_TRAIN_EVIDENCE",
                    "validation_start": test_start.date().isoformat(),
                    "validation_end": test_end.date().isoformat(),
                }
            )
            previous_validation_label_maturity = validation_last_maturity
            continue

        scores = {
            CHAMPION: panel[CHAMPION].astype(float),
            EW5: panel[EW5].astype(float),
            DYNAMIC: dyn._score(panel, dynamic_weights),
        }
        previous_weights: dict[str, dict[str, float]] = {
            contender: {} for contender in CONTENDERS
        }
        rows_by_contender: dict[str, list[dict[str, object]]] = {
            contender: [] for contender in CONTENDERS
        }

        for signal_date in test_dates:
            group = panel.loc[panel["signal_date"] == signal_date]
            for contender in CONTENDERS:
                current = _portfolio_weights(
                    group,
                    scores[contender].loc[group.index],
                    target,
                )
                if current is None:
                    continue
                row = _capacity_row(
                    signal_date=signal_date,
                    previous=previous_weights[contender],
                    current=current,
                    adv_map=adv_map,
                )
                rows_by_contender[contender].append(row)
                previous_weights[contender] = current

        if any(
            len(rows_by_contender[contender]) < wf.MIN_TEST_MONTHS
            for contender in CONTENDERS
        ):
            previous_validation_label_maturity = validation_last_maturity
            continue

        record: dict[str, object] = {
            "fold_id": f"H{horizon}-F{idx}",
            "status": "EVALUATED",
            "validation_start": test_start.date().isoformat(),
            "validation_end": test_end.date().isoformat(),
            "dynamic_weights": dynamic_weights,
        }
        for contender in CONTENDERS:
            record[contender] = _summarize_capacity(rows_by_contender[contender])
        fold_records.append(record)
        previous_validation_label_maturity = validation_last_maturity

    evaluated = [row for row in fold_records if row.get("status") == "EVALUATED"]

    aggregate: dict[str, object] = {}
    for contender in CONTENDERS:
        merged_rows: list[dict[str, object]] = []
        # Re-run row-level extraction from the stored fold summaries is impossible;
        # aggregate fold summaries instead for stable headline comparisons.
        summaries = [fold[contender] for fold in evaluated]
        scenario_summary: dict[str, object] = {}
        for participation in PARTICIPATION_RATES:
            for days in EXECUTION_DAYS:
                key = _scenario_key(participation, days)
                medians = [
                    float(item["scenarios"][key]["median_capacity_try"])  # type: ignore[index]
                    for item in summaries
                    if item["scenarios"][key]["median_capacity_try"] is not None  # type: ignore[index]
                ]
                worsts = [
                    float(item["scenarios"][key]["worst_capacity_try"])  # type: ignore[index]
                    for item in summaries
                    if item["scenarios"][key]["worst_capacity_try"] is not None  # type: ignore[index]
                ]
                support = {}
                for notional in NOTIONALS_TRY:
                    vals = [
                        float(
                            item["scenarios"][key][
                                "support_fraction_by_portfolio_notional_try"
                            ][str(notional)]  # type: ignore[index]
                        )
                        for item in summaries
                    ]
                    support[str(notional)] = (
                        None if not vals else float(np.mean(vals))
                    )
                scenario_summary[key] = {
                    "mean_fold_median_capacity_try": (
                        None if not medians else float(np.mean(medians))
                    ),
                    "worst_capacity_across_folds_try": (
                        None if not worsts else float(np.min(worsts))
                    ),
                    "mean_fold_support_fraction_by_portfolio_notional_try": support,
                }

        aggregate[contender] = {
            "folds": int(len(summaries)),
            "mean_fold_turnover": (
                None
                if not summaries
                else float(np.mean([float(item["mean_gross_turnover"]) for item in summaries]))
            ),
            "mean_fold_selected_adv_coverage": (
                None
                if not summaries
                else float(
                    np.mean(
                        [
                            float(item["selected_adv"]["mean_selected_adv_coverage"])  # type: ignore[index]
                            for item in summaries
                        ]
                    )
                )
            ),
            "total_missing_adv_dates": int(
                sum(int(item["missing_adv_dates"]) for item in summaries)
            ),
            "scenarios": scenario_summary,
        }

    return {
        "all_fold_records": fold_records,
        "evaluated_fold_count": int(len(evaluated)),
        "aggregates": aggregate,
    }


def main() -> int:
    panel, calendar = ew.build_common_panel()
    adv_map, source = load_adv63()

    results = {
        str(horizon): run_horizon(panel, calendar, adv_map, horizon)
        for horizon in HORIZONS
    }

    receipt = {
        "contract": "HISTORICAL_LIQUIDITY_CAPACITY_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "contenders": CONTENDERS,
        "common_panel_rows": int(len(panel)),
        "common_signal_dates": int(panel["signal_date"].nunique()),
        "historical_adv_source": source,
        "adv_definition": "MEAN_63_RAW_CLOSE_TIMES_VOLUME_ENDING_SIGNAL_DATE",
        "capacity_formula": "ADV63_X_PARTICIPATION_X_DAYS_DIV_ABS_DELTA_WEIGHT",
        "participation_rates": PARTICIPATION_RATES,
        "execution_days": EXECUTION_DAYS,
        "illustrative_portfolio_notionals_try": NOTIONALS_TRY,
        "scenario_selection_allowed": False,
        "results": results,
        "limitations": [
            "Daily volume is validated Yahoo-derived market data with official ticker-lineage resolution, not official Borsa daily truth.",
            "Participation rates and execution windows are sensitivity scenarios, not observed execution.",
            "No bid-ask spread, slippage, or market-impact series is fabricated.",
            "Capacity is participation-limited traded-notional capacity only.",
            "No liquidity cutoff, portfolio notional, champion, or production setting is selected from these results.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK."
        ],
    }

    out = Path("research/evidence_runs/historical_liquidity_capacity_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
