"""PIT-safe Confidence / Abstain layer for Zincir Kıran.

Confidence evaluates support for an existing Alpha result. It never mutates the
Alpha value, factor weights, admissions or portfolio sizing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from math import fsum

from .alpha_aggregation import AlphaAggregationSpec
from .alpha_engine import AlphaExecutionStatus, InterpretableAlphaResult
from .baselines import Horizon
from .pit import require_aware_timestamp


class ConfidenceStage(StrEnum):
    CANDIDATE = "CANDIDATE"


class ConfidenceDimensionKind(StrEnum):
    DATA_COVERAGE = "DATA_COVERAGE"
    FRESHNESS = "FRESHNESS"
    PIT_CERTAINTY = "PIT_CERTAINTY"
    FACTOR_EVIDENCE = "FACTOR_EVIDENCE"
    LIQUIDITY = "LIQUIDITY"
    MODEL_AGREEMENT = "MODEL_AGREEMENT"


class ConfidenceAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    STALE = "STALE"


class ConfidenceDecision(StrEnum):
    SIGNAL_ELIGIBLE = "SIGNAL_ELIGIBLE"
    NO_SIGNAL_ALPHA_UNAVAILABLE = "NO_SIGNAL_ALPHA_UNAVAILABLE"
    NO_SIGNAL_REQUIRED_EVIDENCE = "NO_SIGNAL_REQUIRED_EVIDENCE"
    NO_SIGNAL_INSUFFICIENT_COVERAGE = "NO_SIGNAL_INSUFFICIENT_COVERAGE"
    NO_SIGNAL_HARD_FLOOR = "NO_SIGNAL_HARD_FLOOR"
    NO_SIGNAL_LOW_CONFIDENCE = "NO_SIGNAL_LOW_CONFIDENCE"


@dataclass(frozen=True)
class ConfidenceDimensionSpec:
    dimension_id: str
    kind: ConfidenceDimensionKind
    required: bool
    max_age_days: int
    weight: float
    bad_reference: float
    good_reference: float
    hard_floor: float | None = None

    def __post_init__(self) -> None:
        if not self.dimension_id.strip():
            raise ValueError("dimension_id is required")
        if self.max_age_days < 0:
            raise ValueError("max_age_days cannot be negative")
        if not math.isfinite(self.weight) or self.weight <= 0:
            raise ValueError("confidence dimension weight must be finite and positive")
        if not math.isfinite(self.bad_reference) or not math.isfinite(self.good_reference):
            raise ValueError("confidence references must be finite")
        if self.bad_reference == self.good_reference:
            raise ValueError("bad_reference and good_reference must differ")
        if self.hard_floor is not None:
            if not math.isfinite(self.hard_floor) or not 0 <= self.hard_floor <= 1:
                raise ValueError("hard_floor must be in [0, 1]")

    def normalize(self, raw_value: float) -> float:
        if not math.isfinite(raw_value):
            raise ValueError("confidence raw_value must be finite")
        scaled = (raw_value - self.bad_reference) / (
            self.good_reference - self.bad_reference
        )
        return min(1.0, max(0.0, scaled))


@dataclass(frozen=True)
class ConfidenceSpec:
    specification_id: str
    definition_version: str
    horizon: Horizon
    base_alpha_specification_id: str
    base_alpha_definition_version: str
    confidence_protocol_id: str
    universe_rule_version: str
    hypothesis: str
    success_criteria: str
    preregistered_at: datetime
    minimum_weight_coverage: float
    signal_eligibility_threshold: float
    dimensions: tuple[ConfidenceDimensionSpec, ...]
    stage: ConfidenceStage = ConfidenceStage.CANDIDATE

    def __post_init__(self) -> None:
        for name, value in (
            ("specification_id", self.specification_id),
            ("definition_version", self.definition_version),
            ("base_alpha_specification_id", self.base_alpha_specification_id),
            ("base_alpha_definition_version", self.base_alpha_definition_version),
            ("confidence_protocol_id", self.confidence_protocol_id),
            ("universe_rule_version", self.universe_rule_version),
            ("hypothesis", self.hypothesis),
            ("success_criteria", self.success_criteria),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if self.stage is not ConfidenceStage.CANDIDATE:
            raise ValueError("confidence implementation is candidate-only")
        if not 0 < self.minimum_weight_coverage <= 1:
            raise ValueError("minimum_weight_coverage must be in (0, 1]")
        if not 0 <= self.signal_eligibility_threshold <= 1:
            raise ValueError("signal_eligibility_threshold must be in [0, 1]")
        if not self.dimensions:
            raise ValueError("confidence specification requires dimensions")
        if self.dimensions != tuple(
            sorted(self.dimensions, key=lambda item: item.dimension_id)
        ):
            raise ValueError("confidence dimensions must be sorted by dimension_id")
        dimension_ids = tuple(item.dimension_id for item in self.dimensions)
        if len(set(dimension_ids)) != len(dimension_ids):
            raise ValueError("confidence dimension_ids must be unique")


@dataclass
class ConfidenceRegistry:
    _specifications: dict[tuple[str, str], ConfidenceSpec] = field(
        default_factory=dict
    )

    def register(self, specification: ConfidenceSpec) -> None:
        key = (specification.specification_id, specification.definition_version)
        existing = self._specifications.get(key)
        if existing is not None and existing != specification:
            raise ValueError("conflicting confidence specification version")
        self._specifications[key] = specification

    def get(self, specification_id: str, definition_version: str) -> ConfidenceSpec:
        try:
            return self._specifications[(specification_id, definition_version)]
        except KeyError as exc:
            raise KeyError("confidence specification is not registered") from exc


@dataclass(frozen=True)
class ConfidenceObservation:
    observation_id: str
    security_id: str
    dimension_id: str
    confidence_protocol_id: str
    raw_value: float
    window_start: datetime
    window_end: datetime
    available_at: datetime
    source_reference: str

    def __post_init__(self) -> None:
        for name, value in (
            ("observation_id", self.observation_id),
            ("security_id", self.security_id),
            ("dimension_id", self.dimension_id),
            ("confidence_protocol_id", self.confidence_protocol_id),
            ("source_reference", self.source_reference),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not math.isfinite(self.raw_value):
            raise ValueError("confidence raw_value must be finite")
        require_aware_timestamp(self.window_start)
        require_aware_timestamp(self.window_end)
        require_aware_timestamp(self.available_at)
        if self.window_end < self.window_start:
            raise ValueError("confidence window_end cannot precede window_start")
        if self.available_at < self.window_end:
            raise ValueError("confidence available_at cannot precede window_end")


@dataclass(frozen=True)
class ConfidenceDimensionResult:
    dimension_id: str
    kind: ConfidenceDimensionKind
    required: bool
    availability: ConfidenceAvailability
    observation_id: str | None
    raw_value: float | None
    normalized_quality: float | None
    weight: float
    weighted_contribution: float | None
    hard_floor: float | None
    hard_floor_pass: bool | None
    age_days: float | None


@dataclass(frozen=True)
class ConfidenceResult:
    specification_id: str
    definition_version: str
    security_id: str
    horizon: Horizon
    prediction_timestamp: datetime
    source_alpha_specification_id: str
    source_alpha_definition_version: str
    source_alpha_value: float | None
    decision: ConfidenceDecision
    confidence_score: float | None
    evidence_weight_coverage: float
    available_weight: float
    total_weight: float
    dimension_results: tuple[ConfidenceDimensionResult, ...]
    abstention_reasons: tuple[str, ...]


def _evaluate_dimension(
    *,
    dimension: ConfidenceDimensionSpec,
    observation: ConfidenceObservation | None,
    specification: ConfidenceSpec,
    security_id: str,
    prediction_timestamp: datetime,
) -> ConfidenceDimensionResult:
    if observation is None:
        return ConfidenceDimensionResult(
            dimension_id=dimension.dimension_id,
            kind=dimension.kind,
            required=dimension.required,
            availability=ConfidenceAvailability.MISSING,
            observation_id=None,
            raw_value=None,
            normalized_quality=None,
            weight=dimension.weight,
            weighted_contribution=None,
            hard_floor=dimension.hard_floor,
            hard_floor_pass=None,
            age_days=None,
        )
    if observation.dimension_id != dimension.dimension_id:
        raise ValueError("confidence observation dimension mismatch")
    if observation.security_id != security_id:
        raise ValueError("confidence observation security mismatch")
    if observation.confidence_protocol_id != specification.confidence_protocol_id:
        raise ValueError("confidence observation protocol mismatch")
    if (
        observation.window_end > prediction_timestamp
        or observation.available_at > prediction_timestamp
    ):
        raise ValueError("future confidence evidence cannot enter evaluation")

    age_days = (prediction_timestamp - observation.window_end).total_seconds() / 86400
    if age_days > dimension.max_age_days:
        return ConfidenceDimensionResult(
            dimension_id=dimension.dimension_id,
            kind=dimension.kind,
            required=dimension.required,
            availability=ConfidenceAvailability.STALE,
            observation_id=observation.observation_id,
            raw_value=observation.raw_value,
            normalized_quality=None,
            weight=dimension.weight,
            weighted_contribution=None,
            hard_floor=dimension.hard_floor,
            hard_floor_pass=None,
            age_days=age_days,
        )

    quality = dimension.normalize(observation.raw_value)
    return ConfidenceDimensionResult(
        dimension_id=dimension.dimension_id,
        kind=dimension.kind,
        required=dimension.required,
        availability=ConfidenceAvailability.AVAILABLE,
        observation_id=observation.observation_id,
        raw_value=observation.raw_value,
        normalized_quality=quality,
        weight=dimension.weight,
        weighted_contribution=quality * dimension.weight,
        hard_floor=dimension.hard_floor,
        hard_floor_pass=(
            None if dimension.hard_floor is None else quality >= dimension.hard_floor
        ),
        age_days=age_days,
    )


def evaluate_confidence(
    *,
    specification: ConfidenceSpec,
    base_alpha_specification: AlphaAggregationSpec,
    alpha_result: InterpretableAlphaResult,
    observations: list[ConfidenceObservation],
    prediction_timestamp: datetime,
) -> ConfidenceResult:
    """Evaluate support for Alpha without modifying Alpha itself."""
    require_aware_timestamp(prediction_timestamp)
    if specification.preregistered_at > prediction_timestamp:
        raise ValueError("confidence specification was not preregistered by prediction time")
    if specification.horizon is not base_alpha_specification.horizon:
        raise ValueError("confidence horizon does not match base Alpha")
    if (
        specification.base_alpha_specification_id
        != base_alpha_specification.specification_id
        or specification.base_alpha_definition_version
        != base_alpha_specification.definition_version
    ):
        raise ValueError("confidence specification references a different base Alpha")
    if alpha_result.status is AlphaExecutionStatus.SCORED:
        if alpha_result.alpha_value is None or not math.isfinite(alpha_result.alpha_value):
            raise ValueError("SCORED alpha result requires finite alpha_value")
    elif alpha_result.alpha_value is not None:
        raise ValueError("abstained alpha result cannot carry alpha_value")
    if (
        alpha_result.specification_id != base_alpha_specification.specification_id
        or alpha_result.definition_version != base_alpha_specification.definition_version
        or alpha_result.horizon is not specification.horizon
    ):
        raise ValueError("alpha result does not match confidence base Alpha")

    declared_dimensions = {item.dimension_id for item in specification.dimensions}
    observations_by_dimension: dict[str, ConfidenceObservation] = {}
    for observation in observations:
        if observation.dimension_id not in declared_dimensions:
            raise ValueError("confidence observation dimension is not declared")
        if observation.dimension_id in observations_by_dimension:
            raise ValueError("duplicate confidence observation for dimension")
        observations_by_dimension[observation.dimension_id] = observation

    dimension_results = tuple(
        _evaluate_dimension(
            dimension=dimension,
            observation=observations_by_dimension.get(dimension.dimension_id),
            specification=specification,
            security_id=alpha_result.security_id,
            prediction_timestamp=prediction_timestamp,
        )
        for dimension in specification.dimensions
    )

    total_weight = fsum(item.weight for item in dimension_results)
    available = tuple(
        item
        for item in dimension_results
        if item.availability is ConfidenceAvailability.AVAILABLE
    )
    available_weight = fsum(item.weight for item in available)
    coverage = available_weight / total_weight

    required_unavailable = tuple(
        item.dimension_id
        for item in dimension_results
        if item.required and item.availability is not ConfidenceAvailability.AVAILABLE
    )
    hard_floor_failures = tuple(
        item.dimension_id
        for item in available
        if item.hard_floor_pass is False
    )

    reasons: list[str] = []
    score: float | None = None

    if alpha_result.status is not AlphaExecutionStatus.SCORED:
        decision = ConfidenceDecision.NO_SIGNAL_ALPHA_UNAVAILABLE
        reasons.append("ALPHA_UNAVAILABLE")
    elif required_unavailable:
        decision = ConfidenceDecision.NO_SIGNAL_REQUIRED_EVIDENCE
        reasons.extend(f"REQUIRED_EVIDENCE:{item}" for item in required_unavailable)
    elif coverage < specification.minimum_weight_coverage:
        decision = ConfidenceDecision.NO_SIGNAL_INSUFFICIENT_COVERAGE
        reasons.append("INSUFFICIENT_CONFIDENCE_COVERAGE")
    else:
        score = fsum(
            item.weighted_contribution or 0.0
            for item in available
        ) / available_weight
        if hard_floor_failures:
            decision = ConfidenceDecision.NO_SIGNAL_HARD_FLOOR
            reasons.extend(f"HARD_FLOOR:{item}" for item in hard_floor_failures)
        elif score < specification.signal_eligibility_threshold:
            decision = ConfidenceDecision.NO_SIGNAL_LOW_CONFIDENCE
            reasons.append("LOW_CONFIDENCE_SCORE")
        else:
            decision = ConfidenceDecision.SIGNAL_ELIGIBLE

    return ConfidenceResult(
        specification_id=specification.specification_id,
        definition_version=specification.definition_version,
        security_id=alpha_result.security_id,
        horizon=specification.horizon,
        prediction_timestamp=prediction_timestamp,
        source_alpha_specification_id=alpha_result.specification_id,
        source_alpha_definition_version=alpha_result.definition_version,
        source_alpha_value=alpha_result.alpha_value,
        decision=decision,
        confidence_score=score,
        evidence_weight_coverage=coverage,
        available_weight=available_weight,
        total_weight=total_weight,
        dimension_results=dimension_results,
        abstention_reasons=tuple(reasons),
    )
