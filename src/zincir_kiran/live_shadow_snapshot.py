"""Live PIT snapshot contract and prospective shadow execution gate.

The gate validates whether a set of content-addressed snapshots is eligible to
feed Prospective Shadow Protocol v1. It never creates a shadow run.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp
from .prospective_shadow_protocol import (
    DomainObservation,
    ProspectiveShadowTrack,
    ShadowDomainState,
    ShadowTrackDecision,
    evaluate_track_availability,
)


class LiveSnapshotAuthority(StrEnum):
    AUTHORITATIVE_LIVE = "AUTHORITATIVE_LIVE"
    VALIDATED_LIVE_RESEARCH = "VALIDATED_LIVE_RESEARCH"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class LiveSnapshotArtifact:
    snapshot_id: str
    domain_id: str
    source_id: str
    source_url: str
    logical_key: str
    source_available_at: datetime
    captured_at: datetime
    retrieved_at: datetime
    content_sha256: str
    byte_size: int
    authority: LiveSnapshotAuthority

    def __post_init__(self) -> None:
        for name, value in (
            ("snapshot_id", self.snapshot_id),
            ("domain_id", self.domain_id),
            ("source_id", self.source_id),
            ("source_url", self.source_url),
            ("logical_key", self.logical_key),
            ("content_sha256", self.content_sha256),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.source_available_at)
        require_aware_timestamp(self.captured_at)
        require_aware_timestamp(self.retrieved_at)
        if self.source_available_at > self.captured_at:
            raise ValueError("source_available_at cannot follow captured_at")
        if self.retrieved_at < self.captured_at:
            raise ValueError("retrieved_at cannot precede captured_at")
        if self.byte_size < 0:
            raise ValueError("byte_size cannot be negative")
        if len(self.content_sha256) != 64:
            raise ValueError("content_sha256 must be 64 hex characters")
        try:
            int(self.content_sha256, 16)
        except ValueError as exc:
            raise ValueError("content_sha256 must be hexadecimal") from exc


@dataclass(frozen=True)
class ShadowExecutionGateResult:
    track_id: str
    decision: ShadowTrackDecision
    reasons: tuple[str, ...]
    eligible_snapshot_ids: tuple[str, ...]
    manifest_sha256: str


def reject_conflicting_live_snapshots(
    snapshots: Iterable[LiveSnapshotArtifact],
) -> None:
    by_key: dict[str, LiveSnapshotArtifact] = {}
    for snapshot in snapshots:
        prior = by_key.get(snapshot.logical_key)
        if prior is None:
            by_key[snapshot.logical_key] = snapshot
            continue
        if prior.content_sha256 != snapshot.content_sha256:
            raise ValueError(
                f"conflicting live snapshot content for logical_key={snapshot.logical_key}"
            )


def _manifest_hash(
    *,
    activation_at: datetime,
    as_of: datetime,
    executed_at: datetime,
    snapshots: tuple[LiveSnapshotArtifact, ...],
) -> str:
    payload = {
        "activation_at": activation_at.isoformat(),
        "as_of": as_of.isoformat(),
        "executed_at": executed_at.isoformat(),
        "snapshots": [
            {
                "snapshot_id": item.snapshot_id,
                "domain_id": item.domain_id,
                "source_id": item.source_id,
                "source_url": item.source_url,
                "logical_key": item.logical_key,
                "source_available_at": item.source_available_at.isoformat(),
                "captured_at": item.captured_at.isoformat(),
                "retrieved_at": item.retrieved_at.isoformat(),
                "content_sha256": item.content_sha256,
                "byte_size": item.byte_size,
                "authority": item.authority.value,
            }
            for item in snapshots
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate_shadow_execution_gate(
    *,
    track: ProspectiveShadowTrack,
    activation_at: datetime,
    as_of: datetime,
    executed_at: datetime,
    snapshots: Iterable[LiveSnapshotArtifact],
) -> ShadowExecutionGateResult:
    """Validate a track's live snapshot set without creating a shadow run."""
    require_aware_timestamp(activation_at)
    require_aware_timestamp(as_of)
    require_aware_timestamp(executed_at)
    if as_of <= activation_at:
        raise ValueError("shadow as_of must be strictly after protocol activation")
    if executed_at < as_of:
        raise ValueError("shadow execution cannot precede as_of")

    ordered = tuple(
        sorted(
            snapshots,
            key=lambda item: (
                item.domain_id,
                item.logical_key,
                item.snapshot_id,
            ),
        )
    )
    reject_conflicting_live_snapshots(ordered)

    by_domain: dict[str, list[LiveSnapshotArtifact]] = {}
    for item in ordered:
        by_domain.setdefault(item.domain_id, []).append(item)

    observations: list[DomainObservation] = []
    eligible_ids: list[str] = []
    for domain in track.required_domains:
        candidates = by_domain.get(domain, [])
        if not candidates:
            observations.append(
                DomainObservation(
                    domain_id=domain,
                    state=ShadowDomainState.UNAVAILABLE,
                    snapshot_id=None,
                    snapshot_sha256=None,
                    reason_code="NO_LIVE_SNAPSHOT",
                )
            )
            continue

        # Multiple versions for the same domain may coexist only if they use
        # distinct logical keys. The most recently captured candidate that is
        # temporally valid is considered.
        candidates = sorted(
            candidates,
            key=lambda item: (
                item.captured_at,
                item.retrieved_at,
                item.snapshot_id,
            ),
            reverse=True,
        )
        valid_temporal = [
            item
            for item in candidates
            if item.captured_at > activation_at
            and item.source_available_at <= item.captured_at
            and item.captured_at <= as_of
            and item.retrieved_at <= executed_at
        ]
        if not valid_temporal:
            observations.append(
                DomainObservation(
                    domain_id=domain,
                    state=ShadowDomainState.BLOCKED,
                    snapshot_id=None,
                    snapshot_sha256=None,
                    reason_code="TEMPORAL_AUTHORITY_FAILED",
                )
            )
            continue

        candidate = valid_temporal[0]
        if candidate.authority in {
            LiveSnapshotAuthority.DISCOVERY_ONLY,
            LiveSnapshotAuthority.BLOCKED,
        }:
            observations.append(
                DomainObservation(
                    domain_id=domain,
                    state=ShadowDomainState.BLOCKED,
                    snapshot_id=None,
                    snapshot_sha256=None,
                    reason_code=f"AUTHORITY:{candidate.authority.value}",
                )
            )
            continue

        observations.append(
            DomainObservation(
                domain_id=domain,
                state=ShadowDomainState.AVAILABLE,
                snapshot_id=candidate.snapshot_id,
                snapshot_sha256=candidate.content_sha256,
                reason_code=None,
            )
        )
        eligible_ids.append(candidate.snapshot_id)

    decision, reasons = evaluate_track_availability(track, observations)
    manifest_hash = _manifest_hash(
        activation_at=activation_at,
        as_of=as_of,
        executed_at=executed_at,
        snapshots=ordered,
    )
    return ShadowExecutionGateResult(
        track_id=track.track_id,
        decision=decision,
        reasons=reasons,
        eligible_snapshot_ids=tuple(sorted(eligible_ids)),
        manifest_sha256=manifest_hash,
    )
