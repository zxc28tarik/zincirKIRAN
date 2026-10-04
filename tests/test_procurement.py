from datetime import UTC, datetime

import pytest

from zincir_kiran.evidence_phase import EvidenceDomain
from zincir_kiran.procurement import (
    AccessClass,
    PitSuitability,
    ProcurementRoute,
    ProcurementSpecification,
    ProcurementStatus,
    canonical_route_for,
    dataset_build_blockers,
    default_procurement_specification,
)


PREREGISTERED = datetime(2026, 10, 4, 14, 5, tzinfo=UTC)


def test_default_spec_has_exactly_one_canonical_route_per_domain() -> None:
    spec = default_procurement_specification(preregistered_at=PREREGISTERED)
    for domain in EvidenceDomain:
        route = canonical_route_for(spec, domain)
        assert route.canonical is True
        assert route.pit_suitability is PitSuitability.CANONICAL


def test_prices_and_volume_are_blocked_on_official_historical_access() -> None:
    spec = default_procurement_specification(preregistered_at=PREREGISTERED)
    assert canonical_route_for(spec, EvidenceDomain.PRICES).status is ProcurementStatus.BLOCKED_PENDING_ACCESS
    assert canonical_route_for(spec, EvidenceDomain.VOLUME).status is ProcurementStatus.BLOCKED_PENDING_ACCESS
    blockers = dataset_build_blockers(spec)
    assert "PRICES:prices-bist-datastore:BLOCKED_PENDING_ACCESS" in blockers
    assert "VOLUME:volume-bist-datastore:BLOCKED_PENDING_ACCESS" in blockers


def test_kap_line_item_query_is_not_canonical_history() -> None:
    spec = default_procurement_specification(preregistered_at=PREREGISTERED)
    route = next(item for item in spec.routes if item.route_id == "financials-kap-line-item-query")
    assert route.canonical is False
    assert route.pit_suitability is PitSuitability.DISCOVERY_ONLY


def test_financials_require_original_kap_reports() -> None:
    spec = default_procurement_specification(preregistered_at=PREREGISTERED)
    route = canonical_route_for(spec, EvidenceDomain.FINANCIALS)
    assert route.source_id == "kap"
    assert route.route_id == "financials-kap-original-reports"
    assert route.status is ProcurementStatus.BLOCKED_PENDING_EXPORT


def test_canonical_route_must_be_pit_canonical() -> None:
    with pytest.raises(ValueError, match="canonical route must be PIT CANONICAL"):
        ProcurementRoute(
            domain=EvidenceDomain.PRICES,
            route_id="bad",
            source_id="vendor",
            source_surface="adjusted close",
            access_class=AccessClass.OWNER_ACCESS_ENRICHMENT,
            pit_suitability=PitSuitability.CONDITIONAL,
            canonical=True,
            status=ProcurementStatus.ROUTE_LOCKED,
            rationale="bad",
        )


def test_spec_rejects_missing_canonical_domain() -> None:
    base = default_procurement_specification(preregistered_at=PREREGISTERED)
    routes = tuple(route for route in base.routes if route.domain is not EvidenceDomain.VOLUME)
    with pytest.raises(ValueError, match="exactly one canonical route required for VOLUME"):
        ProcurementSpecification(
            specification_id="bad",
            definition_version="v1",
            preregistered_at=PREREGISTERED,
            routes=routes,
            prohibited_shortcuts=base.prohibited_shortcuts,
        )


def test_prohibited_shortcuts_include_pit_leakage_paths() -> None:
    spec = default_procurement_specification(preregistered_at=PREREGISTERED)
    assert "FUTURE_RESTATED_FINANCIALS_BACKFILLED_INTO_PAST" in spec.prohibited_shortcuts
    assert "MISSING_DATA_NEUTRAL_FILL" in spec.prohibited_shortcuts
    assert "SURVIVOR_ONLY_UNIVERSE" in spec.prohibited_shortcuts
