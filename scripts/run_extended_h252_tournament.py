#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_first_equal_weight_multifactor_challenger as ew  # noqa: E402
import run_real_financial_factor_lab as fin  # noqa: E402
import run_real_fixed_ridge_ml_challenger as ml  # noqa: E402
import run_real_price_factor_lab as px  # noqa: E402
import run_real_sector_neutral_decorrelation as sn  # noqa: E402

HORIZON = 252
PRICE_PATH = ROOT / "data/research_sources/pre2021_price_extension_v1/prices_2018-01_2022-08.csv.gz"
MEMBERSHIP_PATH = ROOT / "data/research_sources/pre2021_price_extension_v1/membership_2020-09_2021-07.csv"
PRICE_SHA256 = "e0894027610988651d9ffec6cb53cad5bcfc41ae7dbd132d5e55af06c7afcf5e"
MEMBERSHIP_SHA256 = "ce691744788fb74f8c904b2aa8b34528140d0785e6507989096362bb226c93ab"
TOLERANCE = 1e-12

EXPECTED_ORIGINAL = {
    "HIGH_52W_PROXIMITY": {
        "mean_test_ic": 0.20482198725369197,
        "mean_top_quintile_forward_excess_proxy": 0.05745157888777047,
        "mean_q5_minus_q1": -0.15150824289112388,
    },
    "EW5_COMPOSITE": {
        "mean_test_ic": 0.178283375709639,
        "mean_top_quintile_forward_excess_proxy": 0.06201944685767114,
        "mean_q5_minus_q1": 0.11545631245581615,
    },
    "TRAIN_ONLY_EVIDENCE_WEIGHTED_5F": {
        "mean_test_ic": 0.2232462895764987,
        "mean_top_quintile_forward_excess_proxy": 0.025048632802585208,
        "mean_q5_minus_q1": -0.1236021498031147,
    },
    "FIXED_RIDGE_5F": {
        "mean_test_ic": 0.21829504538949385,
        "mean_top_quintile_forward_excess_proxy": 0.06591811777702579,
        "mean_q5_minus_q1": -0.07883173984696362,
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_local_freeze() -> dict[str, str]:
    observed_price = sha256(PRICE_PATH)
    observed_membership = sha256(MEMBERSHIP_PATH)
    if observed_price != PRICE_SHA256:
        raise RuntimeError(
            f"42C price hash drift expected={PRICE_SHA256} observed={observed_price}"
        )
    if observed_membership != MEMBERSHIP_SHA256:
        raise RuntimeError(
            "42C membership hash drift "
            f"expected={MEMBERSHIP_SHA256} observed={observed_membership}"
        )
    return {
        "price_sha256": observed_price,
        "membership_sha256": observed_membership,
    }


def frozen_index() -> pd.DataFrame:
    frame = fin.csv_from_market("index")
    return px._clean_index(frame)


def early_price_panel(
    membership: pd.DataFrame,
    index_frame: pd.DataFrame,
    routes_by_ticker: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    daily = px._clean_daily(pd.read_csv(PRICE_PATH, compression="gzip", low_memory=False))
    price_panel = px._factor_rows(daily, membership, index_frame)
    price_panel["signal_date"] = pd.to_datetime(price_panel["signal_date"]).dt.normalize()
    price_panel["ticker"] = price_panel["ticker"].astype(str).str.upper()
    price_panel["sector"] = [
        sn.sector_for(routes_by_ticker, ticker, signal)
        for ticker, signal in zip(
            price_panel["ticker"],
            price_panel["signal_date"],
            strict=True,
        )
    ]

    frames: dict[str, pd.DataFrame] = {}
    for factor in ("HIGH_52W_PROXIMITY", "LOW_VOL_63D", "MOM_6_1"):
        frame = price_panel.copy()
        frame["sector_neutral_score"] = sn.sector_neutralize(
            frame,
            factor,
            direction=1.0,
        )
        frames[factor] = frame
    return price_panel, frames


def semantic_index() -> dict[str, list[dict]]:
    rows_by_ticker: dict[str, list[dict]] = defaultdict(list)
    for row in fin.iter_semantic():
        mapped = str(row.get("report_mapping_ticker") or "").strip().upper()
        fact_tickers = {
            str(fact.get("ticker") or "").strip().upper()
            for fact in row.get("facts") or []
            if fact.get("ticker")
        }
        targets = {mapped} if mapped else fact_tickers
        for ticker in targets:
            if ticker:
                rows_by_ticker[ticker].append(row)
    return rows_by_ticker


def early_financial_frames(
    membership: pd.DataFrame,
    routes_by_ticker: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    rows_by_ticker = semantic_index()
    rows: list[dict[str, object]] = []

    for item in membership.itertuples(index=False):
        signal = pd.Timestamp(item.signal_date).normalize()
        ticker = str(item.ticker).upper()
        fact_rows = rows_by_ticker.get(ticker)
        if not fact_rows:
            continue
        by_field = fin.latest_fact_map(fact_rows, signal.date(), ticker)
        factors = fin.materialize_financial_factors(by_field, signal.date())
        rows.append(
            {
                "signal_date": signal,
                "ticker": ticker,
                "sector": sn.sector_for(routes_by_ticker, ticker, signal),
                "operating_margin_acceleration": factors.get(
                    "operating_margin_acceleration"
                ),
                "gross_margin_acceleration": factors.get(
                    "gross_margin_acceleration"
                ),
            }
        )

    panel = pd.DataFrame(rows)
    frames: dict[str, pd.DataFrame] = {}
    for factor in (
        "operating_margin_acceleration",
        "gross_margin_acceleration",
    ):
        frame = panel.copy()
        frame["sector_neutral_score"] = sn.sector_neutralize(
            frame,
            factor,
            direction=1.0,
        )
        frames[factor] = frame
    return frames


def build_early_common_panel(
    calendar: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    membership = px._clean_membership(pd.read_csv(MEMBERSHIP_PATH))
    if membership["signal_date"].nunique() != 11 or len(membership) != 1100:
        raise RuntimeError(
            "42C membership does not contain exactly 11 x 100 historical cells"
        )

    routes = sn.load_sector_routes()
    routes_by_ticker = {
        ticker: group.copy()
        for ticker, group in routes.groupby("ticker", sort=False)
    }

    price_panel, price_frames = early_price_panel(
        membership,
        calendar,
        routes_by_ticker,
    )
    financial_frames = early_financial_frames(
        membership,
        routes_by_ticker,
    )
    frames = {**price_frames, **financial_frames}

    champion = ew.CHAMPION
    base = frames[champion][
        ["signal_date", "ticker", "sector_neutral_score", f"TARGET_{HORIZON}"]
    ].copy()
    base = base.rename(columns={"sector_neutral_score": champion})

    for factor in ew.FACTORS[1:]:
        frame = frames[factor][
            ["signal_date", "ticker", "sector_neutral_score"]
        ].copy()
        frame = frame.rename(columns={"sector_neutral_score": factor})
        base = base.merge(
            frame,
            on=["signal_date", "ticker"],
            how="inner",
            validate="one_to_one",
        )

    common = base.dropna(subset=list(ew.FACTORS)).copy()
    common[ew.COMPOSITE] = sum(
        common[factor].astype(float) * ew.WEIGHTS[factor]
        for factor in ew.FACTORS
    )
    common = common.sort_values(["signal_date", "ticker"]).reset_index(drop=True)

    month_counts = {
        pd.Timestamp(signal).date().isoformat(): {
            "five_factor_rows": int(len(group)),
            "target_252_rows": int(group[f"TARGET_{HORIZON}"].notna().sum()),
        }
        for signal, group in common.groupby("signal_date", sort=True)
    }
    if len(month_counts) != 11:
        raise RuntimeError(f"early common panel month count !=11: {len(month_counts)}")
    bad = {
        signal: counts
        for signal, counts in month_counts.items()
        if counts["target_252_rows"] < 20
    }
    if bad:
        raise RuntimeError(f"early H252 common panel coverage below 20 rows: {bad}")

    coverage = {
        "membership_rows": int(len(membership)),
        "price_panel_rows": int(len(price_panel)),
        "early_common_rows": int(len(common)),
        "early_signal_dates": int(common["signal_date"].nunique()),
        "month_counts": month_counts,
    }
    return common, coverage


def assert_close(actual: float | None, expected: float, label: str) -> None:
    if actual is None or not np.isfinite(float(actual)):
        raise RuntimeError(f"sanity metric unavailable: {label}")
    if abs(float(actual) - expected) > TOLERANCE:
        raise RuntimeError(
            f"original H252 sanity mismatch {label}: "
            f"expected={expected:.17g} actual={float(actual):.17g}"
        )


def original_sanity(
    original: pd.DataFrame,
    calendar: pd.DataFrame,
) -> dict[str, object]:
    result = ml.run_horizon(original, calendar, HORIZON)
    if result["evaluated_fold_count"] != 1:
        raise RuntimeError(
            "original H252 fold count sanity failed: "
            f"{result['evaluated_fold_count']} != 1"
        )

    for contender, expected in EXPECTED_ORIGINAL.items():
        observed = result["aggregates"][contender]
        for metric, value in expected.items():
            assert_close(
                observed[metric],
                value,
                f"{contender}.{metric}",
            )

    return {
        "pass": True,
        "evaluated_fold_count": result["evaluated_fold_count"],
        "aggregates": result["aggregates"],
        "paired_ridge_vs_champion": result["paired_ridge_vs_champion"],
        "paired_ridge_vs_ew5": result["paired_ridge_vs_ew5"],
        "paired_ridge_vs_dynamic": result["paired_ridge_vs_dynamic"],
    }


def main() -> int:
    frozen = verify_local_freeze()
    original, calendar = ew.build_common_panel()
    original["signal_date"] = pd.to_datetime(original["signal_date"]).dt.normalize()

    sanity = original_sanity(original, calendar)

    early, early_coverage = build_early_common_panel(calendar)

    overlap = original[
        ["signal_date", "ticker"]
    ].merge(
        early[["signal_date", "ticker"]],
        on=["signal_date", "ticker"],
        how="inner",
    )
    if not overlap.empty:
        raise RuntimeError(
            f"early/original panel overlap detected: {overlap.head().to_dict('records')}"
        )

    required = list(ew.FACTORS) + [ew.COMPOSITE, f"TARGET_{HORIZON}"]
    extended = pd.concat(
        [
            early[["signal_date", "ticker"] + required],
            original[["signal_date", "ticker"] + required],
        ],
        ignore_index=True,
        sort=False,
    )
    extended = extended.sort_values(["signal_date", "ticker"]).reset_index(drop=True)

    if extended.duplicated(["signal_date", "ticker"]).any():
        raise RuntimeError("extended panel contains duplicate signal/ticker rows")

    if extended["signal_date"].nunique() != 71:
        raise RuntimeError(
            "extended signal-date count must be 71; "
            f"found={extended['signal_date'].nunique()}"
        )

    result = ml.run_horizon(extended, calendar, HORIZON)
    if result["evaluated_fold_count"] < 2:
        raise RuntimeError(
            "extended H252 tournament did not create at least two evaluated folds: "
            f"{result['evaluated_fold_count']}"
        )

    receipt = {
        "contract": "EXTENDED_H252_TOURNAMENT_V1",
        "authority": "EXPERIMENTAL_VERSION_RISK",
        "production_ready": False,
        "automatic_promotion": False,
        "horizon": HORIZON,
        "frozen_extension": frozen,
        "panel": {
            "original_rows": int(len(original)),
            "original_signal_dates": int(original["signal_date"].nunique()),
            "early_rows": int(len(early)),
            "early_signal_dates": int(early["signal_date"].nunique()),
            "extended_rows": int(len(extended)),
            "extended_signal_dates": int(extended["signal_date"].nunique()),
            "early_coverage": early_coverage,
        },
        "original_sanity": sanity,
        "rules": {
            "factors": ew.FACTORS,
            "equal_weights": ew.WEIGHTS,
            "dynamic_rule": "MAX_MATURED_TRAIN_MEAN_IC_ZERO_THEN_NORMALIZE",
            "ridge_penalty": ml.RIDGE_PENALTY,
            "hyperparameter_search": False,
            "minimum_initial_train_months": 18,
            "test_block_months": 6,
            "minimum_test_months": 3,
            "train_label_maturity_purge": True,
            "validation_embargo": True,
            "missingness": "REQUIRE_ALL_5_FACTORS_NO_NEUTRAL_FILL",
        },
        "extended_result": result,
        "limitations": [
            "The pre-2021 price extension is vendor-derived frozen research evidence, not official Borsa daily truth.",
            "Four merger-era historical tickers remain unresolved and are excluded through ordinary missingness rather than guessed.",
            "Financial inputs remain EXPERIMENTAL_VERSION_RISK.",
            "The factor universe was selected in prior research and this is not a virgin external holdout.",
            "No automatic champion or production promotion is authorized."
        ],
    }

    out = ROOT / "research/evidence_runs/extended_h252_tournament_v1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
