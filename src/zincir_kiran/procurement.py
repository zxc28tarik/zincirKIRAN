"""Historical-data procurement decisions for Zincir Kıran.

This module locks which source route is canonical for each evidence domain and
prevents convenient but non-PIT-safe shortcuts from being silently promoted.
It does not authorize purchases.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .evidence_phase import EvidenceDomain
from .pit import require_aware_timestamp


class AccessClass(StrEnum):
    FREE_PUBLIC = "FREE_PUBLIC"
    PAID_OFFICIAL = "PAID_OFFICIAL"
    MANUAL_EXPORT = "MANUAL_EXPORT"
    OWNER_ACCESS_ENRICHMENT = "OWNER_ACCESS_ENRICHMENT"


class PitSuitability(StrEnum):
    CANONICAL = "CANONICAL"
    CONDITIONAL = "CONDITIONAL"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    FORBIDDEN_AS_CANONICAL = "FORBIDDEN_AS_CANONICAL"


class ProcurementStatus(StrEnum):
    ROUTE_LOCKED = "ROUTE_LOCKED"
    BLOCKED_PENDING_ACCESS = "BLOCKED_PENDING_ACCESS"
    BLOCKED_PENDING_EXPORT = "BLOCKED_PENDING_EXPORT"


@dataclass(frozen=True)
class ProcurementRoute:
    domain: EvidenceDomain
    route_id: str
    source_id: str
    source_surface: str
    access_class: AccessClass
    pit_suitability: PitSuitability
    canonical: bool
    status: ProcurementStatus
    rationale: str

    def __post_init__(self) -> None:
        for name, value in (
            ("route_id", self.route_id),
            ("source_id", self.source_id),
            ("source_surface", self.source_surface),
            ("rationale", self.rationale),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.canonical and self.pit_suitability is not PitSuitability.CANONICAL:
            raise ValueError("canonical route must be PIT CANONICAL")
        if (
            self.pit_suitability is PitSuitability.FORBIDDEN_AS_CANONICAL
            and self.canonical
        ):
            raise ValueError("forbidden route cannot be canonical")


@dataclass(frozen=True)
class ProcurementSpecification:
    specification_id: str
    definition_version: str
    preregistered_at: datetime
    routes: tuple[ProcurementRoute, ...]
    prohibited_shortcuts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.specification_id.strip() or not self.definition_version.strip():
            raise ValueError("procurement specification identity is required")
        require_aware_timestamp(self.preregistered_at)
        if self.routes != tuple(
            sorted(self.routes, key=lambda item: (item.domain.value, item.route_id))
        ):
            raise ValueError("routes must be deterministically sorted")
        route_ids = tuple(item.route_id for item in self.routes)
        if len(set(route_ids)) != len(route_ids):
            raise ValueError("route_id values must be unique")
        if self.prohibited_shortcuts != tuple(sorted(set(self.prohibited_shortcuts))):
            raise ValueError("prohibited_shortcuts must be unique and sorted")

        canonical_by_domain: dict[EvidenceDomain, int] = {}
        for route in self.routes:
            if route.canonical:
                canonical_by_domain[route.domain] = canonical_by_domain.get(route.domain, 0) + 1
        for domain in EvidenceDomain:
            if canonical_by_domain.get(domain, 0) != 1:
                raise ValueError(f"exactly one canonical route required for {domain.value}")


def default_procurement_specification(
    *,
    preregistered_at: datetime,
) -> ProcurementSpecification:
    """Return the locked first-dataset procurement plan."""
    routes = (
        ProcurementRoute(
            domain=EvidenceDomain.CORPORATE_ACTIONS,
            route_id="corporate-actions-kap-primary",
            source_id="kap",
            source_surface="Original KAP corporate-action disclosures",
            access_class=AccessClass.FREE_PUBLIC,
            pit_suitability=PitSuitability.CANONICAL,
            canonical=True,
            status=ProcurementStatus.ROUTE_LOCKED,
            rationale=(
                "Original disclosure timestamps preserve when corporate-action "
                "information became public."
            ),
        ),
        ProcurementRoute(
            domain=EvidenceDomain.FINANCIALS,
            route_id="financials-kap-original-reports",
            source_id="kap",
            source_surface="Original KAP financial-report disclosures and attachments",
            access_class=AccessClass.FREE_PUBLIC,
            pit_suitability=PitSuitability.CANONICAL,
            canonical=True,
            status=ProcurementStatus.BLOCKED_PENDING_EXPORT,
            rationale=(
                "Original filings retain publication timing and restatement provenance; "
                "latest-value comparison views are not sufficient for PIT history."
            ),
        ),
        ProcurementRoute(
            domain=EvidenceDomain.FINANCIALS,
            route_id="financials-kap-line-item-query",
            source_id="kap",
            source_surface="KAP Finansal Tablo Kalem Sorgulama",
            access_class=AccessClass.FREE_PUBLIC,
            pit_suitability=PitSuitability.DISCOVERY_ONLY,
            canonical=False,
            status=ProcurementStatus.ROUTE_LOCKED,
            rationale=(
                "KAP states this view uses the latest published current-period values and "
                "does not preserve prior-period correction detail."
            ),
        ),
        ProcurementRoute(
            domain=EvidenceDomain.PRICES,
            route_id="prices-bist-datastore",
            source_id="borsa_istanbul",
            source_surface="Borsa Istanbul DataStore historical Equity Market data",
            access_class=AccessClass.PAID_OFFICIAL,
            pit_suitability=PitSuitability.CANONICAL,
            canonical=True,
            status=ProcurementStatus.BLOCKED_PENDING_ACCESS,
            rationale=(
                "Borsa Istanbul states that specified historical files have been available "
                "only through DataStore since 2015-08-01."
            ),
        ),
        ProcurementRoute(
            domain=EvidenceDomain.PUBLICATION_TIMESTAMPS,
            route_id="publication-time-kap",
            source_id="kap",
            source_surface="KAP disclosure timestamps",
            access_class=AccessClass.FREE_PUBLIC,
            pit_suitability=PitSuitability.CANONICAL,
            canonical=True,
            status=ProcurementStatus.ROUTE_LOCKED,
            rationale="Disclosure timestamp is the PIT availability anchor for KAP filings.",
        ),
        ProcurementRoute(
            domain=EvidenceDomain.UNIVERSE_HISTORY,
            route_id="universe-bist-reference",
            source_id="borsa_istanbul",
            source_surface="Borsa Istanbul official listing/reference files",
            access_class=AccessClass.FREE_PUBLIC,
            pit_suitability=PitSuitability.CANONICAL,
            canonical=True,
            status=ProcurementStatus.ROUTE_LOCKED,
            rationale=(
                "Official listing/reference records anchor first-trade, ticker-change and "
                "historical investable-universe reconstruction."
            ),
        ),
        ProcurementRoute(
            domain=EvidenceDomain.VOLUME,
            route_id="volume-bist-datastore",
            source_id="borsa_istanbul",
            source_surface="Borsa Istanbul DataStore historical Equity Market data",
            access_class=AccessClass.PAID_OFFICIAL,
            pit_suitability=PitSuitability.CANONICAL,
            canonical=True,
            status=ProcurementStatus.BLOCKED_PENDING_ACCESS,
            rationale=(
                "Historical official market-volume coverage shares the same DataStore "
                "procurement dependency as historical prices."
            ),
        ),
    )
    return ProcurementSpecification(
        specification_id="first-actual-dataset-v1",
        definition_version="v1",
        preregistered_at=preregistered_at,
        routes=tuple(sorted(routes, key=lambda item: (item.domain.value, item.route_id))),
        prohibited_shortcuts=tuple(
            sorted(
                (
                    "ADJUSTED_CLOSE_WITHOUT_CORPORATE_ACTION_PROVENANCE",
                    "FUTURE_RESTATED_FINANCIALS_BACKFILLED_INTO_PAST",
                    "KAP_LATEST_LINE_ITEM_VIEW_AS_CANONICAL_HISTORY",
                    "MISSING_DATA_NEUTRAL_FILL",
                    "SURVIVOR_ONLY_UNIVERSE",
                    "UNDOCUMENTED_VENDOR_EXPORT_WITHOUT_TIMESTAMP_PROVENANCE",
                )
            )
        ),
    )


def canonical_route_for(
    specification: ProcurementSpecification,
    domain: EvidenceDomain,
) -> ProcurementRoute:
    return next(route for route in specification.routes if route.domain is domain and route.canonical)


def dataset_build_blockers(
    specification: ProcurementSpecification,
) -> tuple[str, ...]:
    blockers = [
        f"{route.domain.value}:{route.route_id}:{route.status.value}"
        for route in specification.routes
        if route.canonical and route.status is not ProcurementStatus.ROUTE_LOCKED
    ]
    return tuple(sorted(blockers))
