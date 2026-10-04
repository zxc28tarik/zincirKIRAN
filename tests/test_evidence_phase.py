from datetime import UTC, datetime

import pytest

from zincir_kiran.evidence_phase import (
    DomainCoverage,
    EvidenceDomain,
    SnapshotReadiness,
    SnapshotReadinessSpec,
    SourceArtifact,
    build_pit_snapshot_manifest,
)

PREREG = datetime(2026, 10, 4, 10, 0, tzinfo=UTC)
AS_OF = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
CREATED = datetime(2026, 10, 4, 12, 5, tzinfo=UTC)


def spec() -> SnapshotReadinessSpec:
    return SnapshotReadinessSpec(
        specification_id="real-pit-v1",
        definition_version="v1",
        preregistered_at=PREREG,
        minimum_domain_coverage=(
            (EvidenceDomain.CORPORATE_ACTIONS, 0.90),
            (EvidenceDomain.FINANCIALS, 0.90),
            (EvidenceDomain.PRICES, 0.95),
            (EvidenceDomain.PUBLICATION_TIMESTAMPS, 0.90),
            (EvidenceDomain.UNIVERSE_HISTORY, 0.95),
            (EvidenceDomain.VOLUME, 0.95),
        ),
    )


def artifact(
    artifact_id: str,
    logical_key: str,
    domain: EvidenceDomain,
    content: bytes = b"abc",
    source_id: str = "kap",
) -> SourceArtifact:
    return SourceArtifact.from_bytes(
        artifact_id=artifact_id,
        source_id=source_id,
        source_url="https://example.invalid/source",
        domain=domain,
        retrieved_at=CREATED,
        content=content,
        logical_key=logical_key,
        source_published_at=AS_OF,
    )


def full_coverage() -> list[DomainCoverage]:
    return [
        DomainCoverage(domain, 100, 100, 8, 8)
        for domain in EvidenceDomain
    ]


def test_exact_bytes_produce_exact_hash() -> None:
    first = artifact("a1", "kap:AAA:2026Q2", EvidenceDomain.FINANCIALS, b"one")
    second = artifact("a2", "kap:AAA:2026Q3", EvidenceDomain.FINANCIALS, b"two")
    assert first.content_sha256 != second.content_sha256
    assert first.byte_size == 3


def test_unregistered_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="unregistered source_id"):
        build_pit_snapshot_manifest(
            snapshot_id="snapshot-1",
            created_at=CREATED,
            as_of=AS_OF,
            artifacts=[
                artifact(
                    "a1",
                    "unknown:AAA",
                    EvidenceDomain.PRICES,
                    source_id="unknown",
                )
            ],
            domain_coverage=full_coverage(),
            readiness_spec=spec(),
            allowed_source_ids={"kap", "borsa_istanbul"},
        )


def test_conflicting_logical_artifacts_are_rejected() -> None:
    with pytest.raises(ValueError, match="conflicting content"):
        build_pit_snapshot_manifest(
            snapshot_id="snapshot-1",
            created_at=CREATED,
            as_of=AS_OF,
            artifacts=[
                artifact("a1", "kap:AAA:2026Q2", EvidenceDomain.FINANCIALS, b"one"),
                artifact("a2", "kap:AAA:2026Q2", EvidenceDomain.FINANCIALS, b"two"),
            ],
            domain_coverage=full_coverage(),
            readiness_spec=spec(),
            allowed_source_ids={"kap"},
        )


def test_missing_domain_blocks_snapshot_with_exact_gap() -> None:
    coverage = [
        row for row in full_coverage()
        if row.domain is not EvidenceDomain.PUBLICATION_TIMESTAMPS
    ]
    manifest = build_pit_snapshot_manifest(
        snapshot_id="snapshot-1",
        created_at=CREATED,
        as_of=AS_OF,
        artifacts=[],
        domain_coverage=coverage,
        readiness_spec=spec(),
        allowed_source_ids={"kap", "borsa_istanbul"},
    )
    assert manifest.readiness is SnapshotReadiness.BLOCKED_WITH_GAPS
    assert manifest.gap_reasons == (
        "MISSING_DOMAIN:PUBLICATION_TIMESTAMPS",
    )


def test_low_coverage_blocks_without_neutral_fill() -> None:
    coverage = full_coverage()
    coverage = [
        DomainCoverage(row.domain, 50, 100, row.observed_periods, row.required_periods)
        if row.domain is EvidenceDomain.FINANCIALS
        else row
        for row in coverage
    ]
    manifest = build_pit_snapshot_manifest(
        snapshot_id="snapshot-1",
        created_at=CREATED,
        as_of=AS_OF,
        artifacts=[],
        domain_coverage=coverage,
        readiness_spec=spec(),
        allowed_source_ids={"kap", "borsa_istanbul"},
    )
    assert manifest.readiness is SnapshotReadiness.BLOCKED_WITH_GAPS
    assert manifest.gap_reasons == (
        "INSUFFICIENT_COVERAGE:FINANCIALS:0.500000<0.900000",
    )


def test_full_coverage_is_tournament_ready_and_deterministic() -> None:
    artifacts = [
        artifact("b", "bist:prices:2026-10-04", EvidenceDomain.PRICES, b"prices", "borsa_istanbul"),
        artifact("a", "kap:financials:AAA:2026Q2", EvidenceDomain.FINANCIALS, b"financials"),
    ]
    first = build_pit_snapshot_manifest(
        snapshot_id="snapshot-1",
        created_at=CREATED,
        as_of=AS_OF,
        artifacts=artifacts,
        domain_coverage=full_coverage(),
        readiness_spec=spec(),
        allowed_source_ids={"kap", "borsa_istanbul"},
    )
    second = build_pit_snapshot_manifest(
        snapshot_id="snapshot-1",
        created_at=CREATED,
        as_of=AS_OF,
        artifacts=list(reversed(artifacts)),
        domain_coverage=list(reversed(full_coverage())),
        readiness_spec=spec(),
        allowed_source_ids={"borsa_istanbul", "kap"},
    )
    assert first.readiness is SnapshotReadiness.TOURNAMENT_READY
    assert first.gap_reasons == ()
    assert first.manifest_sha256 == second.manifest_sha256


def test_snapshot_creation_must_follow_preregistration() -> None:
    with pytest.raises(ValueError, match="follow readiness preregistration"):
        build_pit_snapshot_manifest(
            snapshot_id="snapshot-1",
            created_at=PREREG,
            as_of=PREREG,
            artifacts=[],
            domain_coverage=full_coverage(),
            readiness_spec=spec(),
            allowed_source_ids={"kap"},
        )
