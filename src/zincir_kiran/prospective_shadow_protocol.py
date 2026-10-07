"""Prospective-only shadow protocol primitives.

This module defines the temporal and data-authority boundary for the first real
Zincir Kıran shadow protocol. It creates no live runs and performs no broker action.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Iterable

from .pit import require_aware_timestamp


class ShadowTrackDecision(StrEnum):
    SIGNAL_ELIGIBLE = "SIGNAL_ELIGIBLE"
    NO_SIGNAL = "NO_SIGNAL"
    DATA_BLOCKED = "DATA_BLOCKED"
    FACTOR_UNAVAILABLE = "FACTOR_UNAVAILABLE"


class ShadowDomainState(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ProspectiveShadowTrack:
    track_id: str
    kind: str
    required_domains: tuple[str, ...]
    optional_domains: tuple[str, ...]
    missing_policy: str

    def __post_init__(self) -> None:
        if not self.track_id.strip() or not self.kind.strip():
            raise ValueError("track identity is required")
        if self.required_domains != tuple(sorted(set(self.required_domains))):
            raise ValueError("required_domains must be unique and sorted")
        if self.optional_domains != tuple(sorted(set(self.optional_domains))):
            raise ValueError("optional_domains must be unique and sorted")
        if set(self.required_domains) & set(self.optional_domains):
            raise ValueError("required and optional domains cannot overlap")
        if self.missing_policy != "ABSTAIN":
            raise ValueError("prospective shadow missing policy must be ABSTAIN")


@dataclass(frozen=True)
class ProspectiveShadowProtocol:
    protocol_id: str
    definition_version: str
    activation_rule: str
    horizons: tuple[str, ...]
    tracks: tuple[ProspectiveShadowTrack, ...]
    historical_backfill_allowed: bool
    broker_actions_allowed: bool
    orders_allowed: bool
    production_promotion_allowed: bool
    production_thresholds_defined: bool

    def __post_init__(self) -> None:
        if not self.protocol_id.strip() or not self.definition_version.strip():
            raise ValueError("protocol identity is required")
        if self.activation_rule != "FIRST_MAIN_MERGE_COMMIT_CONTAINING_THIS_PROTOCOL":
            raise ValueError("unexpected activation rule")
        if self.horizons != ("H20", "H60", "H120", "H252"):
            raise ValueError("shadow horizons must be exactly H20/H60/H120/H252")
        ids = tuple(track.track_id for track in self.tracks)
        if ids != tuple(sorted(ids)):
            raise ValueError("tracks must be sorted by track_id")
        if len(set(ids)) != len(ids):
            raise ValueError("track ids must be unique")
        if self.historical_backfill_allowed:
            raise ValueError("historical shadow backfill is forbidden")
        if self.broker_actions_allowed or self.orders_allowed:
            raise ValueError("shadow protocol cannot permit broker/order actions")
        if self.production_promotion_allowed:
            raise ValueError("shadow protocol cannot promote production")
        if self.production_thresholds_defined:
            raise ValueError("production thresholds are not defined in shadow v1")


@dataclass(frozen=True)
class DomainObservation:
    domain_id: str
    state: ShadowDomainState
    snapshot_id: str | None
    snapshot_sha256: str | None
    reason_code: str | None

    def __post_init__(self) -> None:
        if not self.domain_id.strip():
            raise ValueError("domain_id is required")
        if self.state is ShadowDomainState.AVAILABLE:
            if not self.snapshot_id or not self.snapshot_sha256:
                raise ValueError("available domain requires immutable snapshot identity")
            if len(self.snapshot_sha256) != 64:
                raise ValueError("snapshot_sha256 must be 64 hex characters")
            try:
                int(self.snapshot_sha256, 16)
            except ValueError as exc:
                raise ValueError("snapshot_sha256 must be hexadecimal") from exc
            if self.reason_code is not None:
                raise ValueError("available domain cannot carry a failure reason")
        else:
            if self.snapshot_id is not None or self.snapshot_sha256 is not None:
                raise ValueError("unavailable/blocked domain cannot masquerade as snapshot")
            if not self.reason_code:
                raise ValueError("unavailable/blocked domain requires reason_code")


def validate_prospective_temporal_boundary(
    *,
    activation_at: datetime,
    as_of: datetime,
    executed_at: datetime,
) -> None:
    """Forbid every shadow run at or before protocol activation."""
    require_aware_timestamp(activation_at)
    require_aware_timestamp(as_of)
    require_aware_timestamp(executed_at)
    if as_of <= activation_at:
        raise ValueError("shadow as_of must be strictly after protocol activation")
    if executed_at < as_of:
        raise ValueError("shadow execution cannot precede as_of")


def evaluate_track_availability(
    track: ProspectiveShadowTrack,
    observations: Iterable[DomainObservation],
) -> tuple[ShadowTrackDecision, tuple[str, ...]]:
    by_domain = {item.domain_id: item for item in observations}
    reasons: list[str] = []
    blocked = False
    unavailable = False

    for domain in track.required_domains:
        item = by_domain.get(domain)
        if item is None:
            unavailable = True
            reasons.append(f"MISSING_DOMAIN:{domain}")
        elif item.state is ShadowDomainState.BLOCKED:
            blocked = True
            reasons.append(f"BLOCKED_DOMAIN:{domain}:{item.reason_code}")
        elif item.state is ShadowDomainState.UNAVAILABLE:
            unavailable = True
            reasons.append(f"UNAVAILABLE_DOMAIN:{domain}:{item.reason_code}")

    if blocked:
        return ShadowTrackDecision.DATA_BLOCKED, tuple(sorted(reasons))
    if unavailable:
        return ShadowTrackDecision.FACTOR_UNAVAILABLE, tuple(sorted(reasons))
    return ShadowTrackDecision.SIGNAL_ELIGIBLE, ()


def canonical_protocol_hash(protocol: ProspectiveShadowProtocol) -> str:
    payload = {
        "protocol_id": protocol.protocol_id,
        "definition_version": protocol.definition_version,
        "activation_rule": protocol.activation_rule,
        "horizons": protocol.horizons,
        "tracks": [
            {
                "track_id": track.track_id,
                "kind": track.kind,
                "required_domains": track.required_domains,
                "optional_domains": track.optional_domains,
                "missing_policy": track.missing_policy,
            }
            for track in protocol.tracks
        ],
        "historical_backfill_allowed": protocol.historical_backfill_allowed,
        "broker_actions_allowed": protocol.broker_actions_allowed,
        "orders_allowed": protocol.orders_allowed,
        "production_promotion_allowed": protocol.production_promotion_allowed,
        "production_thresholds_defined": protocol.production_thresholds_defined,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
