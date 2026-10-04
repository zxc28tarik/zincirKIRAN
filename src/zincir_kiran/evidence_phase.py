"""Evidence-phase primitives for real point-in-time dataset snapshots.

This module turns externally acquired source artifacts into immutable, deterministic
snapshot manifests. It never fabricates missing evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class EvidenceDomain(StrEnum):
    PRICES = "PRICES"
    VOLUME = "VOLUME"
    FINANCIALS = "FINANCIALS"
    PUBLICATION_TIMESTAMPS = "PUBLICATION_TIMESTAMPS"
    CORPORATE_ACTIONS = "CORPORATE_ACTIONS"
    UNIVERSE_HISTORY = "UNIVERSE_HISTORY"


class SnapshotReadiness(StrEnum):
    TOURNAMENT_READY = "TOURNAMENT_READY"
    BLOCKED_WITH_GAPS = "BLOCKED_WITH_GAPS"


@dataclass(frozen=True)
class SourceArtifact:
    artifact_id: str
    source_id: str
    source_url: str
    domain: EvidenceDomain
    retrieved_at: datetime
    content_sha256: str
    byte_size: int
    logical_key: str
    source_published_at: datetime | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("artifact_id", self.artifact_id),
            ("source_id", self.source_id),
            ("source_url", self.source_url),
            ("content_sha256", self.content_sha256),
            ("logical_key", self.logical_key),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.retrieved_at)
        if self.source_published_at is not None:
            require_aware_timestamp(self.source_published_at)
            if self.source_published_at > self.retrieved_at:
                raise ValueError("source_published_at cannot follow retrieved_at")
        if self.byte_size < 0:
            raise ValueError("byte_size cannot be negative")
        if len(self.content_sha256) != 64:
            raise ValueError("content_sha256 must be a SHA-256 hex digest")
        try:
            int(self.content_sha256, 16)
        except ValueError as exc:
            raise ValueError("content_sha256 must be hexadecimal") from exc

    @classmethod
    def from_bytes(
        cls,
        *,
        artifact_id: str,
        source_id: str,
        source_url: str,
        domain: EvidenceDomain,
        retrieved_at: datetime,
        content: bytes,
        logical_key: str,
        source_published_at: datetime | None = None,
    ) -> SourceArtifact:
        return cls(
            artifact_id=artifact_id,
            source_id=source_id,
            source_url=source_url,
            domain=domain,
            retrieved_at=retrieved_at,
            content_sha256=hashlib.sha256(content).hexdigest(),
            byte_size=len(content),
            logical_key=logical_key,
            source_published_at=source_published_at,
        )


@dataclass(frozen=True)
class DomainCoverage:
    domain: EvidenceDomain
    observed_securities: int
    required_securities: int
    observed_periods: int
    required_periods: int

    def __post_init__(self) -> None:
        for name, value in (
            ("observed_securities", self.observed_securities),
            ("required_securities", self.required_securities),
            ("observed_periods", self.observed_periods),
            ("required_periods", self.required_periods),
        ):
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.observed_securities > self.required_securities:
            raise ValueError("observed_securities cannot exceed required_securities")
        if self.observed_periods > self.required_periods:
            raise ValueError("observed_periods cannot exceed required_periods")

    @property
    def security_coverage(self) -> float | None:
        if self.required_securities == 0:
            return None
        return self.observed_securities / self.required_securities

    @property
    def period_coverage(self) -> float | None:
        if self.required_periods == 0:
            return None
        return self.observed_periods / self.required_periods

    @property
    def joint_coverage(self) -> float | None:
        security = self.security_coverage
        periods = self.period_coverage
        if security is None or periods is None:
            return None
        return min(security, periods)


@dataclass(frozen=True)
class SnapshotReadinessSpec:
    specification_id: str
    definition_version: str
    preregistered_at: datetime
    minimum_domain_coverage: tuple[tuple[EvidenceDomain, float], ...]

    def __post_init__(self) -> None:
        if not self.specification_id.strip() or not self.definition_version.strip():
            raise ValueError("snapshot readiness identity is required")
        require_aware_timestamp(self.preregistered_at)
        domains = tuple(domain for domain, _ in self.minimum_domain_coverage)
        if domains != tuple(sorted(domains, key=lambda item: item.value)):
            raise ValueError("minimum_domain_coverage must be sorted by domain")
        if len(set(domains)) != len(domains):
            raise ValueError("minimum_domain_coverage domains must be unique")
        for _, threshold in self.minimum_domain_coverage:
            if not math.isfinite(threshold) or not 0 <= threshold <= 1:
                raise ValueError("coverage thresholds must be finite in [0, 1]")


@dataclass(frozen=True)
class PitSnapshotManifest:
    snapshot_id: str
    created_at: datetime
    as_of: datetime
    source_artifacts: tuple[SourceArtifact, ...]
    domain_coverage: tuple[DomainCoverage, ...]
    readiness: SnapshotReadiness
    gap_reasons: tuple[str, ...]
    manifest_sha256: str

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id is required")
        require_aware_timestamp(self.created_at)
        require_aware_timestamp(self.as_of)
        if self.created_at < self.as_of:
            raise ValueError("snapshot cannot be created before as_of")
        if self.source_artifacts != tuple(
            sorted(self.source_artifacts, key=lambda item: (item.logical_key, item.artifact_id))
        ):
            raise ValueError("source_artifacts must be deterministically sorted")
        if self.domain_coverage != tuple(
            sorted(self.domain_coverage, key=lambda item: item.domain.value)
        ):
            raise ValueError("domain_coverage must be deterministically sorted")
        if self.gap_reasons != tuple(sorted(set(self.gap_reasons))):
            raise ValueError("gap_reasons must be unique and sorted")
        if self.readiness is SnapshotReadiness.TOURNAMENT_READY and self.gap_reasons:
            raise ValueError("tournament-ready snapshot cannot have gaps")
        if self.readiness is SnapshotReadiness.BLOCKED_WITH_GAPS and not self.gap_reasons:
            raise ValueError("blocked snapshot must explain gaps")


def validate_source_registry(
    artifacts: Iterable[SourceArtifact],
    *,
    allowed_source_ids: set[str],
) -> None:
    for artifact in artifacts:
        if artifact.source_id not in allowed_source_ids:
            raise ValueError(f"unregistered source_id: {artifact.source_id}")


def reject_conflicting_logical_artifacts(
    artifacts: Iterable[SourceArtifact],
) -> None:
    by_key: dict[str, SourceArtifact] = {}
    for artifact in artifacts:
        existing = by_key.get(artifact.logical_key)
        if existing is None:
            by_key[artifact.logical_key] = artifact
            continue
        if existing.content_sha256 != artifact.content_sha256:
            raise ValueError(
                f"conflicting content for logical artifact {artifact.logical_key}"
            )


def _canonical_manifest_hash(
    *,
    snapshot_id: str,
    as_of: datetime,
    artifacts: tuple[SourceArtifact, ...],
    coverage: tuple[DomainCoverage, ...],
    readiness: SnapshotReadiness,
    gap_reasons: tuple[str, ...],
) -> str:
    payload = {
        "snapshot_id": snapshot_id,
        "as_of": as_of.isoformat(),
        "artifacts": [
            {
                "artifact_id": item.artifact_id,
                "source_id": item.source_id,
                "source_url": item.source_url,
                "domain": item.domain.value,
                "retrieved_at": item.retrieved_at.isoformat(),
                "source_published_at": (
                    item.source_published_at.isoformat()
                    if item.source_published_at is not None
                    else None
                ),
                "content_sha256": item.content_sha256,
                "byte_size": item.byte_size,
                "logical_key": item.logical_key,
            }
            for item in artifacts
        ],
        "coverage": [
            {
                "domain": item.domain.value,
                "observed_securities": item.observed_securities,
                "required_securities": item.required_securities,
                "observed_periods": item.observed_periods,
                "required_periods": item.required_periods,
            }
            for item in coverage
        ],
        "readiness": readiness.value,
        "gap_reasons": gap_reasons,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_pit_snapshot_manifest(
    *,
    snapshot_id: str,
    created_at: datetime,
    as_of: datetime,
    artifacts: list[SourceArtifact],
    domain_coverage: list[DomainCoverage],
    readiness_spec: SnapshotReadinessSpec,
    allowed_source_ids: set[str],
) -> PitSnapshotManifest:
    require_aware_timestamp(created_at)
    require_aware_timestamp(as_of)
    if created_at <= readiness_spec.preregistered_at:
        raise ValueError("snapshot creation must follow readiness preregistration")
    if created_at < as_of:
        raise ValueError("snapshot cannot be created before as_of")

    validate_source_registry(artifacts, allowed_source_ids=allowed_source_ids)
    reject_conflicting_logical_artifacts(artifacts)

    ordered_artifacts = tuple(
        sorted(artifacts, key=lambda item: (item.logical_key, item.artifact_id))
    )
    ordered_coverage = tuple(
        sorted(domain_coverage, key=lambda item: item.domain.value)
    )
    coverage_by_domain = {item.domain: item for item in ordered_coverage}

    gaps: list[str] = []
    for domain, threshold in readiness_spec.minimum_domain_coverage:
        coverage = coverage_by_domain.get(domain)
        if coverage is None:
            gaps.append(f"MISSING_DOMAIN:{domain.value}")
            continue
        joint = coverage.joint_coverage
        if joint is None:
            gaps.append(f"UNDEFINED_COVERAGE:{domain.value}")
        elif joint < threshold:
            gaps.append(
                f"INSUFFICIENT_COVERAGE:{domain.value}:{joint:.6f}<{threshold:.6f}"
            )

    gap_reasons = tuple(sorted(gaps))
    readiness = (
        SnapshotReadiness.TOURNAMENT_READY
        if not gap_reasons
        else SnapshotReadiness.BLOCKED_WITH_GAPS
    )
    manifest_hash = _canonical_manifest_hash(
        snapshot_id=snapshot_id,
        as_of=as_of,
        artifacts=ordered_artifacts,
        coverage=ordered_coverage,
        readiness=readiness,
        gap_reasons=gap_reasons,
    )
    return PitSnapshotManifest(
        snapshot_id=snapshot_id,
        created_at=created_at,
        as_of=as_of,
        source_artifacts=ordered_artifacts,
        domain_coverage=ordered_coverage,
        readiness=readiness,
        gap_reasons=gap_reasons,
        manifest_sha256=manifest_hash,
    )
