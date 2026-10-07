#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research/evidence_runs"
OUT = EVIDENCE / "real_shadow_readiness_inventory_v1.json"

REQUIRED = {
    "financial_version": EVIDENCE / "financial_version_authority_v1.json",
    "corporate_actions": EVIDENCE / "corporate_action_event_bootstrap_v1.json",
    "historical_market": EVIDENCE / "historical_market_bootstrap_v1.json",
    "membership_backcast": EVIDENCE / "bist100_membership_backcast_2019_2021_summary_v1.json",
    "price_freeze": EVIDENCE / "pre2021_price_extension_freeze_summary_v1.json",
    "walk_forward": EVIDENCE / "real_walk_forward_factor_stability_summary_v1.json",
    "h252_tournament": EVIDENCE / "extended_h252_tournament_summary_v1.json",
    "h252_portfolio": EVIDENCE / "extended_h252_portfolio_realism_summary_v1.json",
    "cost_sensitivity": EVIDENCE / "long_only_cost_sensitivity_summary_v1.json",
    "capacity": EVIDENCE / "historical_liquidity_capacity_summary_v1.json",
}

VALID = {"VERIFIED_READY", "RESEARCH_ONLY", "MISSING", "BLOCKED"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_receipts() -> tuple[dict[str, dict], dict[str, dict]]:
    data: dict[str, dict] = {}
    sources: dict[str, dict] = {}
    for key, path in REQUIRED.items():
        if not path.exists():
            raise RuntimeError(f"required evidence receipt missing: {path}")
        data[key] = json.loads(path.read_text(encoding="utf-8"))
        sources[key] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha(path),
        }
    return data, sources


def item(
    dimension: str,
    status: str,
    reason: str,
    source_keys: list[str],
    sources: dict[str, dict],
) -> dict:
    if status not in VALID:
        raise RuntimeError(f"invalid inventory status: {status}")
    return {
        "dimension": dimension,
        "status": status,
        "reason": reason,
        "evidence": [sources[key] for key in source_keys],
    }


def main() -> int:
    r, sources = load_receipts()

    # Fail closed if important receipt semantics drift.
    fv = r["financial_version"]
    if fv.get("bulk_latest_only_authorized_for_historical_pit") is not False:
        raise RuntimeError("financial-version authority semantic drift")
    if fv.get("exhaustive_5y_version_enumeration_complete") is not False:
        raise RuntimeError("financial version inventory unexpectedly claims completion")

    ca = r["corporate_actions"]
    if ca.get("dividend_catalog_complete") is not False:
        raise RuntimeError("corporate-action receipt semantic drift")
    if ca.get("detail_subtype_evidence", {}).get("ex_date_materialized") is not False:
        raise RuntimeError("corporate-action ex-date authority unexpectedly changed")

    h252 = r["h252_tournament"]
    if h252.get("evaluated_fold_count") != 2:
        raise RuntimeError("extended H252 evidence no longer has exactly two evaluated folds")

    portfolio = r["h252_portfolio"]
    if portfolio.get("evaluated_fold_count") != 2:
        raise RuntimeError("extended H252 portfolio evidence no longer has two folds")
    if portfolio.get("original_sanity", {}).get("pass") is not True:
        raise RuntimeError("extended H252 portfolio sanity is not PASS")

    market = r["historical_market"]
    market_authorities = {
        artifact.get("authority")
        for artifact in market.get("artifacts", [])
    }
    if "VALIDATED_DERIVED_MARKET_DATA" not in market_authorities:
        raise RuntimeError("historical market authority semantic drift")

    capacity = r["capacity"]
    coverage = []
    for horizon in ("H20", "H60", "H120", "H252"):
        agg = capacity.get("results", {}).get(horizon, {}).get("aggregates", {})
        for contender in agg.values():
            value = contender.get("mean_fold_selected_adv_coverage")
            if value is not None:
                coverage.append(float(value))
    if not coverage or min(coverage) < 1.0:
        raise RuntimeError("expected complete selected-name ADV coverage is not present")

    inventory = [
        item(
            "UNIVERSE_HISTORY",
            "VERIFIED_READY",
            "Tested BIST100 historical membership is auditable, fail-closed, and round-trip verified; the 2020-09..2021-07 extension is frozen.",
            ["membership_backcast", "price_freeze"],
            sources,
        ),
        item(
            "HISTORICAL_PRICES",
            "RESEARCH_ONLY",
            "Historical stock prices are frozen and hash-pinned for research but remain Yahoo/vendor-derived rather than full official Borsa daily price authority.",
            ["historical_market", "price_freeze"],
            sources,
        ),
        item(
            "VOLUME_LIQUIDITY",
            "RESEARCH_ONLY",
            "Dated ADV63 coverage is complete for tested portfolios, but volume authority is validated derived market data rather than official Borsa daily truth.",
            ["capacity", "historical_market"],
            sources,
        ),
        item(
            "FINANCIAL_PIT_AUTHORITY",
            "BLOCKED",
            "Bulk latest-only financial history is explicitly unauthorized for historical PIT and exhaustive superseded-version enumeration remains incomplete.",
            ["financial_version"],
            sources,
        ),
        item(
            "PUBLICATION_REVISION_AUTHORITY",
            "BLOCKED",
            "A real correction regression case proves version timing matters; the complete enumerated historical revision chain is not yet authoritative.",
            ["financial_version"],
            sources,
        ),
        item(
            "CORPORATE_ACTION_AUTHORITY",
            "BLOCKED",
            "Corporate-action inventory is broad but dividend catalog, ratios/cash amounts, ex-dates and payment dates are incomplete.",
            ["corporate_actions"],
            sources,
        ),
        item(
            "RESEARCH_REPLAY_INTEGRITY",
            "VERIFIED_READY",
            "Frozen data hashes, original-result sanity gates, and extended H252 one-fold replay checks pass before opening new evidence.",
            ["price_freeze", "h252_tournament", "h252_portfolio"],
            sources,
        ),
        item(
            "LIVE_SHADOW_REPLAY_INTEGRITY",
            "MISSING",
            "No prospective live shadow run receipt exists yet; research replay does not substitute for live shadow replay.",
            [],
            sources,
        ),
        item(
            "COST_MODEL_AUTHORITY",
            "BLOCKED",
            "10/25/50 bps values are transparent sensitivity scenarios, not observed historical spread/slippage/market-impact execution costs.",
            ["cost_sensitivity", "h252_portfolio"],
            sources,
        ),
        item(
            "CAPACITY_EVIDENCE",
            "RESEARCH_ONLY",
            "Historical ADV participation capacity is available with complete selected-name coverage, but source volume remains derived research evidence.",
            ["capacity", "h252_portfolio"],
            sources,
        ),
        item(
            "SELF_FINANCING_NAV_DRAWDOWN",
            "MISSING",
            "Current long-leg diagnostics use overlapping forward-return proxies and explicitly do not claim a self-financing NAV backtest; no comparable max-drawdown receipt exists.",
            ["h252_portfolio", "cost_sensitivity"],
            sources,
        ),
        item(
            "PROSPECTIVE_SHADOW_PROTOCOL",
            "MISSING",
            "Shadow primitives and schemas exist in code, but no real prospective protocol tied to current data/model versions has been preregistered.",
            [],
            sources,
        ),
        item(
            "PROSPECTIVE_SHADOW_RUNS",
            "MISSING",
            "No prospective trading-day shadow receipts have been recorded.",
            [],
            sources,
        ),
        item(
            "REALIZED_SHADOW_LABELS",
            "MISSING",
            "No prospective shadow horizon labels have matured and been attached.",
            [],
            sources,
        ),
        item(
            "PRODUCTION_THRESHOLDS_PREREGISTERED",
            "MISSING",
            "Research Constitution intentionally leaves exact production thresholds unlocked; none may be selected post hoc from current results.",
            [],
            sources,
        ),
    ]

    statuses = {row["dimension"]: row["status"] for row in inventory}
    production_blockers = sorted(
        row["dimension"]
        for row in inventory
        if row["status"] in {"BLOCKED", "MISSING"}
    )

    # Protocol design can proceed because the research engine and immutable
    # research receipts exist, but execution of a real shadow program remains
    # blocked until a prospective protocol and live-source snapshot path exist.
    decision = {
        "shadow_preparation": "PROTOCOL_DESIGN_READY",
        "shadow_execution": "BLOCKED",
        "historical_shadow_backfill": "FORBIDDEN",
        "production_eligibility": "BLOCKED",
        "automatic_deployment": False,
        "production_threshold_selection": "FORBIDDEN_IN_THIS_IMPLEMENTATION",
        "next_required_work": [
            "PREREGISTER_PROSPECTIVE_SHADOW_PROTOCOL",
            "LOCK_LIVE_POINT_IN_TIME_DATA_SNAPSHOT_PATH",
            "DO_NOT_BACKFILL_SHADOW_HISTORY",
        ],
    }

    receipt = {
        "contract": "REAL_SHADOW_READINESS_INVENTORY_V1",
        "authority": "EVIDENCE_INVENTORY_ONLY",
        "production_ready": False,
        "performance_recomputed": False,
        "exact_production_thresholds_selected": False,
        "source_receipts": sources,
        "inventory": inventory,
        "status_by_dimension": statuses,
        "production_blockers": production_blockers,
        "decision": decision,
        "key_research_state": {
            "extended_h252_folds": h252["evaluated_fold_count"],
            "extended_h252_portfolio_folds": portfolio["evaluated_fold_count"],
            "financial_version_enumeration_complete": fv[
                "exhaustive_5y_version_enumeration_complete"
            ],
            "corporate_action_dividend_catalog_complete": ca[
                "dividend_catalog_complete"
            ],
            "minimum_observed_selected_adv_coverage": min(coverage),
        },
        "limitations": [
            "This receipt inventories evidence authority; it is not a production gate threshold evaluation.",
            "Research-only vendor data cannot be promoted to official production authority by this inventory.",
            "Prospective shadow must begin prospectively after a protocol is preregistered; backfill is forbidden.",
        ],
    }

    OUT.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
