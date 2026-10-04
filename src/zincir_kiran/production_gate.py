"""Fail-closed production decision gate for Zincir Kıran.

This module decides research readiness only. It never places orders, connects to a
broker, or automatically promotes any model to production.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class ProductionDecision(StrEnum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    EXTEND_SHADOW = "EXTEND_SHADOW"
    PRODUCTION_ELIGIBLE_REVIEW_REQUIRED = "PRODUCTION_ELIGIBLE_REVIEW_REQUIRED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ProductionGateSpec:
    gate_id: str
    definition_version: str
    preregistered_at: datetime
    minimum_shadow_days: int
    minimum_shadow_runs: int
    minimum_realized_label_coverage: float
    minimum_mean_ic: float
    minimum_net_return_after_costs: float
    maximum_drawdown: float
    minimum_liquidity_fit: float
    require_replay_integrity: bool = True
    require_pit_integrity: bool = True
    require_cost_model: bool = True
    require_capacity_evidence: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("gate_id", self.gate_id),
            ("definition_version", self.definition_version),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if self.minimum_shadow_days < 0 or self.minimum_shadow_runs < 0:
            raise ValueError("shadow minimums cannot be negative")
        for name, value in (
            ("minimum_realized_label_coverage", self.minimum_realized_label_coverage),
            ("minimum_liquidity_fit", self.minimum_liquidity_fit),
        ):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be finite in [0, 1]")
        for name, value in (
            ("minimum_mean_ic", self.minimum_mean_ic),
            ("minimum_net_return_after_costs", self.minimum_net_return_after_costs),
            ("maximum_drawdown", self.maximum_drawdown),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.maximum_drawdown < 0:
            raise ValueError("maximum_drawdown must be non-negative")


@dataclass(frozen=True)
class ProductionEvidence:
    evaluated_at: datetime
    tournament_run_id: str | None
    shadow_protocol_id: str | None
    shadow_days: int | None
    shadow_runs: int | None
    realized_label_coverage: float | None
    mean_ic: float | None
    net_return_after_costs: float | None
    max_drawdown: float | None
    liquidity_fit: float | None
    replay_integrity: bool | None
    pit_integrity: bool | None
    cost_model_present: bool | None
    capacity_evidence_present: bool | None

    def __post_init__(self) -> None:
        require_aware_timestamp(self.evaluated_at)
        if self.shadow_days is not None and self.shadow_days < 0:
            raise ValueError("shadow_days cannot be negative")
        if self.shadow_runs is not None and self.shadow_runs < 0:
            raise ValueError("shadow_runs cannot be negative")
        for name, value in (
            ("realized_label_coverage", self.realized_label_coverage),
            ("liquidity_fit", self.liquidity_fit),
        ):
            if value is not None and (not math.isfinite(value) or not 0 <= value <= 1):
                raise ValueError(f"{name} must be finite in [0, 1] when provided")
        for name, value in (
            ("mean_ic", self.mean_ic),
            ("net_return_after_costs", self.net_return_after_costs),
            ("max_drawdown", self.max_drawdown),
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite when provided")
        if self.max_drawdown is not None and self.max_drawdown < 0:
            raise ValueError("max_drawdown must be non-negative")


@dataclass(frozen=True)
class ProductionGateOutcome:
    gate_id: str
    definition_version: str
    evaluated_at: datetime
    decision: ProductionDecision
    review_required: bool
    automatic_deployment: bool
    failed_checks: tuple[str, ...]
    missing_evidence: tuple[str, ...]


def evaluate_production_gate(
    specification: ProductionGateSpec,
    evidence: ProductionEvidence,
) -> ProductionGateOutcome:
    """Evaluate preregistered evidence with fail-closed precedence."""
    if evidence.evaluated_at <= specification.preregistered_at:
        raise ValueError("production evaluation must follow preregistration")

    missing: list[str] = []
    for name, value in (
        ("tournament_run_id", evidence.tournament_run_id),
        ("shadow_protocol_id", evidence.shadow_protocol_id),
        ("shadow_days", evidence.shadow_days),
        ("shadow_runs", evidence.shadow_runs),
        ("realized_label_coverage", evidence.realized_label_coverage),
        ("mean_ic", evidence.mean_ic),
        ("net_return_after_costs", evidence.net_return_after_costs),
        ("max_drawdown", evidence.max_drawdown),
        ("liquidity_fit", evidence.liquidity_fit),
    ):
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(name)

    if specification.require_replay_integrity and evidence.replay_integrity is None:
        missing.append("replay_integrity")
    if specification.require_pit_integrity and evidence.pit_integrity is None:
        missing.append("pit_integrity")
    if specification.require_cost_model and evidence.cost_model_present is None:
        missing.append("cost_model_present")
    if specification.require_capacity_evidence and evidence.capacity_evidence_present is None:
        missing.append("capacity_evidence_present")

    missing_tuple = tuple(sorted(set(missing)))
    if missing_tuple:
        return ProductionGateOutcome(
            gate_id=specification.gate_id,
            definition_version=specification.definition_version,
            evaluated_at=evidence.evaluated_at,
            decision=ProductionDecision.RESEARCH_ONLY,
            review_required=True,
            automatic_deployment=False,
            failed_checks=(),
            missing_evidence=missing_tuple,
        )

    failed_integrity: list[str] = []
    if specification.require_replay_integrity and evidence.replay_integrity is not True:
        failed_integrity.append("replay_integrity")
    if specification.require_pit_integrity and evidence.pit_integrity is not True:
        failed_integrity.append("pit_integrity")
    if specification.require_cost_model and evidence.cost_model_present is not True:
        failed_integrity.append("cost_model_present")
    if (
        specification.require_capacity_evidence
        and evidence.capacity_evidence_present is not True
    ):
        failed_integrity.append("capacity_evidence_present")

    if failed_integrity:
        return ProductionGateOutcome(
            gate_id=specification.gate_id,
            definition_version=specification.definition_version,
            evaluated_at=evidence.evaluated_at,
            decision=ProductionDecision.REJECTED,
            review_required=True,
            automatic_deployment=False,
            failed_checks=tuple(sorted(failed_integrity)),
            missing_evidence=(),
        )

    assert evidence.shadow_days is not None
    assert evidence.shadow_runs is not None
    assert evidence.realized_label_coverage is not None
    if (
        evidence.shadow_days < specification.minimum_shadow_days
        or evidence.shadow_runs < specification.minimum_shadow_runs
        or evidence.realized_label_coverage < specification.minimum_realized_label_coverage
    ):
        shadow_failures: list[str] = []
        if evidence.shadow_days < specification.minimum_shadow_days:
            shadow_failures.append("minimum_shadow_days")
        if evidence.shadow_runs < specification.minimum_shadow_runs:
            shadow_failures.append("minimum_shadow_runs")
        if evidence.realized_label_coverage < specification.minimum_realized_label_coverage:
            shadow_failures.append("minimum_realized_label_coverage")
        return ProductionGateOutcome(
            gate_id=specification.gate_id,
            definition_version=specification.definition_version,
            evaluated_at=evidence.evaluated_at,
            decision=ProductionDecision.EXTEND_SHADOW,
            review_required=True,
            automatic_deployment=False,
            failed_checks=tuple(sorted(shadow_failures)),
            missing_evidence=(),
        )

    assert evidence.mean_ic is not None
    assert evidence.net_return_after_costs is not None
    assert evidence.max_drawdown is not None
    assert evidence.liquidity_fit is not None

    failed_performance: list[str] = []
    if evidence.mean_ic < specification.minimum_mean_ic:
        failed_performance.append("minimum_mean_ic")
    if evidence.net_return_after_costs < specification.minimum_net_return_after_costs:
        failed_performance.append("minimum_net_return_after_costs")
    if evidence.max_drawdown > specification.maximum_drawdown:
        failed_performance.append("maximum_drawdown")
    if evidence.liquidity_fit < specification.minimum_liquidity_fit:
        failed_performance.append("minimum_liquidity_fit")

    if failed_performance:
        return ProductionGateOutcome(
            gate_id=specification.gate_id,
            definition_version=specification.definition_version,
            evaluated_at=evidence.evaluated_at,
            decision=ProductionDecision.REJECTED,
            review_required=True,
            automatic_deployment=False,
            failed_checks=tuple(sorted(failed_performance)),
            missing_evidence=(),
        )

    return ProductionGateOutcome(
        gate_id=specification.gate_id,
        definition_version=specification.definition_version,
        evaluated_at=evidence.evaluated_at,
        decision=ProductionDecision.PRODUCTION_ELIGIBLE_REVIEW_REQUIRED,
        review_required=True,
        automatic_deployment=False,
        failed_checks=(),
        missing_evidence=(),
    )
