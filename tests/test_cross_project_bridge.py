import pytest

from zincir_kiran.cross_project_bridge import (
    ReuseAuthority,
    default_total_rasyo_bootstrap_manifest,
    require_canonical_pit,
)
from zincir_kiran.evidence_phase import EvidenceDomain


def test_m3_index_closes_and_sector_routes_are_canonical_pit() -> None:
    manifest = default_total_rasyo_bootstrap_manifest()
    index_prices = next(
        item
        for item in manifest.artifacts
        if item.source_path.endswith("index_closes.csv.gz")
    )
    routes = next(
        item
        for item in manifest.artifacts
        if item.source_path.endswith("sector_routes.csv.gz")
    )
    assert index_prices.evidence_domain is EvidenceDomain.PRICES
    assert routes.evidence_domain is EvidenceDomain.UNIVERSE_HISTORY
    assert index_prices.authority is ReuseAuthority.CANONICAL_PIT
    assert routes.authority is ReuseAuthority.CANONICAL_PIT
    require_canonical_pit(index_prices)
    require_canonical_pit(routes)


def test_financial_archives_do_not_silently_become_authoritative_pit() -> None:
    manifest = default_total_rasyo_bootstrap_manifest()
    raw = next(
        item for item in manifest.artifacts
        if "acquisition_receipt.run_33568804543.json" in item.source_path
    )
    discovery = next(
        item for item in manifest.artifacts
        if "insurance_finance_full28_schema_receipt" in item.source_path
    )
    assert raw.authority is ReuseAuthority.RAW_EVIDENCE_ONLY
    assert discovery.authority is ReuseAuthority.DISCOVERY_ONLY
    with pytest.raises(ValueError, match="not authorized for canonical PIT"):
        require_canonical_pit(raw)
    with pytest.raises(ValueError, match="not authorized for canonical PIT"):
        require_canonical_pit(discovery)


def test_corporate_action_inventory_is_positive_event_only() -> None:
    manifest = default_total_rasyo_bootstrap_manifest()
    ca = next(
        item for item in manifest.artifacts
        if item.source_path.endswith("w6_ca_gate_reachability_v1/receipt.json")
    )
    assert ca.evidence_domain is EvidenceDomain.CORPORATE_ACTIONS
    assert ca.authority is ReuseAuthority.POSITIVE_EVENT_ONLY
    with pytest.raises(ValueError):
        require_canonical_pit(ca)


def test_total_rasyo_scores_are_explicitly_prohibited_as_targets() -> None:
    manifest = default_total_rasyo_bootstrap_manifest()
    assert "DERIVED_TOTAL_RASYO_SCORE_AS_TARGET" in manifest.prohibited_source_products
    assert "M2_SCORE_AS_FORWARD_RETURN_LABEL" in manifest.prohibited_source_products


def test_all_cross_repo_refs_pin_full_commit_sha() -> None:
    manifest = default_total_rasyo_bootstrap_manifest()
    assert all(len(item.source_commit) == 40 for item in manifest.artifacts)
