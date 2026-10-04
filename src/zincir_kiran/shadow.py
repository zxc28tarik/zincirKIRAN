"""Immutable live shadow-mode receipts for Zincir Kıran.

Shadow mode records what the system actually knew and decided at an exact timestamp.
It never places orders and never promotes a model to production.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from .baselines import Horizon
from .pit import require_aware_timestamp


class ShadowDecision(StrEnum):
    SIGNAL_ELIGIBLE = "SIGNAL_ELIGIBLE"
    NO_SIGNAL = "NO_SIGNAL"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True)
class ShadowProtocol:
    protocol_id: str
    definition_version: str
    universe_rule_version: str
    alpha_specification_id: str
    alpha_definition_version: str
    confidence_specification_id: str
    confidence_definition_version: str
    ml_challenger_id: str | None
    ml_definition_version: str | None
    preregistered_at: datetime
    horizons: tuple[Horizon, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("protocol_id", self.protocol_id),
            ("definition_version", self.definition_version),
            ("universe_rule_version", self.universe_rule_version),
            ("alpha_specification_id", self.alpha_specification_id),
            ("alpha_definition_version", self.alpha_definition_version),
            ("confidence_specification_id", self.confidence_specification_id),
            ("confidence_definition_version", self.confidence_definition_version),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if bool(self.ml_challenger_id) != bool(self.ml_definition_version):
            raise ValueError("ML challenger id/version must appear together")
        if not self.horizons:
            raise ValueError("shadow protocol requires at least one horizon")
        if self.horizons != tuple(sorted(set(self.horizons), key=lambda item: item.value)):
            raise ValueError("horizons must be unique and sorted")


@dataclass(frozen=True)
class ShadowSecurityDecision:
    security_id: str
    decision: ShadowDecision
    alpha_score: float | None
    confidence_score: float | None
    ml_score: float | None
    portfolio_target_weight: float | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.security_id.strip():
            raise ValueError("security_id is required")
        for value in (
            self.alpha_score,
            self.confidence_score,
            self.ml_score,
            self.portfolio_target_weight,
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError("shadow numeric outputs must be finite when present")
        if self.portfolio_target_weight is not None and self.portfolio_target_weight < 0:
            raise ValueError("portfolio_target_weight cannot be negative")
        if (
            self.decision is not ShadowDecision.SIGNAL_ELIGIBLE
            and self.portfolio_target_weight not in (None, 0.0)
        ):
            raise ValueError("NO_SIGNAL/ABSTAIN cannot carry positive portfolio intent")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError("reason_codes must be unique and sorted")


@dataclass(frozen=True)
class ShadowRun:
    shadow_run_id: str
    protocol_id: str
    definition_version: str
    as_of: datetime
    executed_at: datetime
    data_snapshot_id: str
    universe_snapshot_id: str
    decisions: tuple[ShadowSecurityDecision, ...]
    input_receipt_hash: str
    output_receipt_hash: str

    def __post_init__(self) -> None:
        for name, value in (
            ("shadow_run_id", self.shadow_run_id),
            ("protocol_id", self.protocol_id),
            ("definition_version", self.definition_version),
            ("data_snapshot_id", self.data_snapshot_id),
            ("universe_snapshot_id", self.universe_snapshot_id),
            ("input_receipt_hash", self.input_receipt_hash),
            ("output_receipt_hash", self.output_receipt_hash),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.as_of)
        require_aware_timestamp(self.executed_at)
        if self.executed_at < self.as_of:
            raise ValueError("shadow execution cannot precede as_of")
        security_ids = tuple(item.security_id for item in self.decisions)
        if security_ids != tuple(sorted(security_ids)) or len(set(security_ids)) != len(security_ids):
            raise ValueError("shadow decisions must be unique and sorted by security_id")


@dataclass(frozen=True)
class ShadowRealizedLabel:
    shadow_run_id: str
    security_id: str
    horizon: Horizon
    label_available_at: datetime
    market_relative_total_return: float

    def __post_init__(self) -> None:
        if not self.shadow_run_id.strip() or not self.security_id.strip():
            raise ValueError("shadow_run_id and security_id are required")
        require_aware_timestamp(self.label_available_at)
        if not math.isfinite(self.market_relative_total_return):
            raise ValueError("realized label must be finite")


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_shadow_run(
    *,
    protocol: ShadowProtocol,
    shadow_run_id: str,
    as_of: datetime,
    executed_at: datetime,
    data_snapshot_id: str,
    universe_snapshot_id: str,
    input_provenance: dict[str, str],
    decisions: list[ShadowSecurityDecision],
) -> ShadowRun:
    """Create an immutable deterministic shadow receipt."""
    require_aware_timestamp(as_of)
    require_aware_timestamp(executed_at)
    if as_of < protocol.preregistered_at:
        raise ValueError("shadow run cannot predate protocol preregistration")
    if executed_at < as_of:
        raise ValueError("shadow execution cannot precede as_of")
    if not data_snapshot_id.strip() or not universe_snapshot_id.strip():
        raise ValueError("data and universe snapshot ids are required")
    if not input_provenance or any(not key.strip() or not value.strip() for key, value in input_provenance.items()):
        raise ValueError("input provenance must be explicit and non-empty")

    ordered = tuple(sorted(decisions, key=lambda item: item.security_id))
    if len({item.security_id for item in ordered}) != len(ordered):
        raise ValueError("duplicate security decision")

    input_receipt_hash = _canonical_hash(
        {
            "protocol_id": protocol.protocol_id,
            "definition_version": protocol.definition_version,
            "as_of": as_of.isoformat(),
            "data_snapshot_id": data_snapshot_id,
            "universe_snapshot_id": universe_snapshot_id,
            "input_provenance": input_provenance,
        }
    )
    output_receipt_hash = _canonical_hash(
        [
            {
                "security_id": item.security_id,
                "decision": item.decision.value,
                "alpha_score": item.alpha_score,
                "confidence_score": item.confidence_score,
                "ml_score": item.ml_score,
                "portfolio_target_weight": item.portfolio_target_weight,
                "reason_codes": item.reason_codes,
            }
            for item in ordered
        ]
    )
    return ShadowRun(
        shadow_run_id=shadow_run_id,
        protocol_id=protocol.protocol_id,
        definition_version=protocol.definition_version,
        as_of=as_of,
        executed_at=executed_at,
        data_snapshot_id=data_snapshot_id,
        universe_snapshot_id=universe_snapshot_id,
        decisions=ordered,
        input_receipt_hash=input_receipt_hash,
        output_receipt_hash=output_receipt_hash,
    )


def verify_shadow_replay(
    stored: ShadowRun,
    reproduced: ShadowRun,
) -> None:
    """Reject a replay that does not reproduce the immutable original receipt."""
    if stored.protocol_id != reproduced.protocol_id:
        raise ValueError("shadow replay protocol mismatch")
    if stored.definition_version != reproduced.definition_version:
        raise ValueError("shadow replay definition mismatch")
    if stored.as_of != reproduced.as_of:
        raise ValueError("shadow replay as_of mismatch")
    if stored.data_snapshot_id != reproduced.data_snapshot_id:
        raise ValueError("shadow replay data snapshot mismatch")
    if stored.universe_snapshot_id != reproduced.universe_snapshot_id:
        raise ValueError("shadow replay universe snapshot mismatch")
    if stored.input_receipt_hash != reproduced.input_receipt_hash:
        raise ValueError("shadow replay input receipt mismatch")
    if stored.output_receipt_hash != reproduced.output_receipt_hash:
        raise ValueError("shadow replay output receipt mismatch")


def attach_realized_label(
    *,
    run: ShadowRun,
    security_id: str,
    horizon: Horizon,
    label_available_at: datetime,
    market_relative_total_return: float,
    minimum_calendar_days: int | None = None,
) -> ShadowRealizedLabel:
    """Attach a label only after it can legitimately exist.

    minimum_calendar_days is deliberately explicit because trading-day calendars
    belong to data/infrastructure, not to this primitive.
    """
    require_aware_timestamp(label_available_at)
    if security_id not in {item.security_id for item in run.decisions}:
        raise ValueError("realized label security was not present in shadow run")
    minimum_days = horizon.value if minimum_calendar_days is None else minimum_calendar_days
    if minimum_days < 0:
        raise ValueError("minimum_calendar_days cannot be negative")
    earliest = run.as_of + timedelta(days=minimum_days)
    if label_available_at < earliest:
        raise ValueError("realized label is premature")
    return ShadowRealizedLabel(
        shadow_run_id=run.shadow_run_id,
        security_id=security_id,
        horizon=horizon,
        label_available_at=label_available_at,
        market_relative_total_return=market_relative_total_return,
    )
