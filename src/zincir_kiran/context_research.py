"""PIT-safe regime, contradiction and interaction research layer.

This module produces candidate context evidence only. It does not mutate Alpha,
factor admission, portfolio construction or confidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from .alpha_aggregation import AlphaAggregationSpec
from .alpha_engine import AlphaFactorWeight, validate_weight_plan
from .baselines import Horizon
from .interpretable_alpha import FactorAdmission
from .pit import require_aware_timestamp


class ContextStage(StrEnum):
    CANDIDATE = "CANDIDATE"


class ContextRunStatus(StrEnum):
    EVALUATED = "EVALUATED"
    ABSTAIN_INSUFFICIENT_REGIME = "ABSTAIN_INSUFFICIENT_REGIME"
    ABSTAIN_INSUFFICIENT_FACTOR_SIGNALS = "ABSTAIN_INSUFFICIENT_FACTOR_SIGNALS"


class RegimeAvailability(StrEnum):
    CLASSIFIED = "CLASSIFIED"
    MISSING = "MISSING"
    STALE = "STALE"


class InteractionState(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE_REGIME = "INACTIVE_REGIME"


@dataclass(frozen=True)
class RegimeStateRule:
    state_id: str
    lower_inclusive: float | None
    upper_exclusive: float | None

    def __post_init__(self) -> None:
        if not self.state_id.strip():
            raise ValueError("state_id is required")
        if self.lower_inclusive is not None and not math.isfinite(self.lower_inclusive):
            raise ValueError("lower_inclusive must be finite when provided")
        if self.upper_exclusive is not None and not math.isfinite(self.upper_exclusive):
            raise ValueError("upper_exclusive must be finite when provided")
        if (
            self.lower_inclusive is not None
            and self.upper_exclusive is not None
            and self.lower_inclusive >= self.upper_exclusive
        ):
            raise ValueError("regime state lower bound must be below upper bound")

    def matches(self, value: float) -> bool:
        if not math.isfinite(value):
            raise ValueError("regime observation value must be finite")
        if self.lower_inclusive is not None and value < self.lower_inclusive:
            return False
        return self.upper_exclusive is None or value < self.upper_exclusive


def _state_sort_key(rule: RegimeStateRule) -> tuple[float, float, str]:
    lower = -math.inf if rule.lower_inclusive is None else rule.lower_inclusive
    upper = math.inf if rule.upper_exclusive is None else rule.upper_exclusive
    return (lower, upper, rule.state_id)


@dataclass(frozen=True)
class RegimeDimensionSpec:
    dimension_id: str
    max_age_days: int
    state_rules: tuple[RegimeStateRule, ...]

    def __post_init__(self) -> None:
        if not self.dimension_id.strip():
            raise ValueError("dimension_id is required")
        if self.max_age_days < 0:
            raise ValueError("max_age_days cannot be negative")
        if not self.state_rules:
            raise ValueError("regime dimension requires state rules")
        if self.state_rules != tuple(sorted(self.state_rules, key=_state_sort_key)):
            raise ValueError("regime state rules must use canonical interval ordering")

        state_ids = tuple(rule.state_id for rule in self.state_rules)
        if len(set(state_ids)) != len(state_ids):
            raise ValueError("regime state_ids must be unique")

        previous_upper: float | None = None
        for index, rule in enumerate(self.state_rules):
            if index > 0 and previous_upper is None:
                raise ValueError("unbounded regime state cannot be followed by another state")
            if (
                index > 0
                and rule.lower_inclusive is not None
                and previous_upper is not None
                and rule.lower_inclusive < previous_upper
            ):
                raise ValueError("regime state intervals cannot overlap")
            previous_upper = rule.upper_exclusive


@dataclass(frozen=True)
class ContradictionRule:
    rule_id: str
    left_admission_id: str
    right_admission_id: str
    minimum_absolute_signal: float
    required_regime_states: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("rule_id", self.rule_id),
            ("left_admission_id", self.left_admission_id),
            ("right_admission_id", self.right_admission_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.left_admission_id == self.right_admission_id:
            raise ValueError("contradiction rule requires two distinct admissions")
        if (
            not math.isfinite(self.minimum_absolute_signal)
            or self.minimum_absolute_signal < 0
        ):
            raise ValueError("minimum_absolute_signal must be finite and non-negative")
        if self.required_regime_states != tuple(sorted(set(self.required_regime_states))):
            raise ValueError("required_regime_states must be unique and sorted")


@dataclass(frozen=True)
class InteractionRule:
    rule_id: str
    left_admission_id: str
    right_admission_id: str
    required_regime_states: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("rule_id", self.rule_id),
            ("left_admission_id", self.left_admission_id),
            ("right_admission_id", self.right_admission_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.left_admission_id == self.right_admission_id:
            raise ValueError("interaction rule requires two distinct admissions")
        if self.required_regime_states != tuple(sorted(set(self.required_regime_states))):
            raise ValueError("required_regime_states must be unique and sorted")


@dataclass(frozen=True)
class ContextResearchSpec:
    specification_id: str
    definition_version: str
    horizon: Horizon
    base_alpha_specification_id: str
    base_alpha_definition_version: str
    context_protocol_id: str
    universe_rule_version: str
    hypothesis: str
    success_criteria: str
    preregistered_at: datetime
    regime_dimensions: tuple[RegimeDimensionSpec, ...]
    contradiction_rules: tuple[ContradictionRule, ...]
    interaction_rules: tuple[InteractionRule, ...]
    stage: ContextStage = ContextStage.CANDIDATE

    def __post_init__(self) -> None:
        for name, value in (
            ("specification_id", self.specification_id),
            ("definition_version", self.definition_version),
            ("base_alpha_specification_id", self.base_alpha_specification_id),
            ("base_alpha_definition_version", self.base_alpha_definition_version),
            ("context_protocol_id", self.context_protocol_id),
            ("universe_rule_version", self.universe_rule_version),
            ("hypothesis", self.hypothesis),
            ("success_criteria", self.success_criteria),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if self.stage is not ContextStage.CANDIDATE:
            raise ValueError("context research implementation is candidate-only")
        if not self.regime_dimensions:
            raise ValueError("context research requires at least one regime dimension")
        if (
            self.regime_dimensions
            != tuple(sorted(self.regime_dimensions, key=lambda item: item.dimension_id))
        ):
            raise ValueError("regime dimensions must be sorted by dimension_id")
        dimension_ids = tuple(item.dimension_id for item in self.regime_dimensions)
        if len(set(dimension_ids)) != len(dimension_ids):
            raise ValueError("regime dimension_ids must be unique")

        if (
            self.contradiction_rules
            != tuple(sorted(self.contradiction_rules, key=lambda item: item.rule_id))
        ):
            raise ValueError("contradiction rules must be sorted by rule_id")
        if (
            self.interaction_rules
            != tuple(sorted(self.interaction_rules, key=lambda item: item.rule_id))
        ):
            raise ValueError("interaction rules must be sorted by rule_id")
        contradiction_ids = tuple(item.rule_id for item in self.contradiction_rules)
        interaction_ids = tuple(item.rule_id for item in self.interaction_rules)
        if len(set(contradiction_ids)) != len(contradiction_ids):
            raise ValueError("contradiction rule_ids must be unique")
        if len(set(interaction_ids)) != len(interaction_ids):
            raise ValueError("interaction rule_ids must be unique")

        declared_states = {
            (dimension.dimension_id, state_rule.state_id)
            for dimension in self.regime_dimensions
            for state_rule in dimension.state_rules
        }
        for rule in (*self.contradiction_rules, *self.interaction_rules):
            unknown_requirements = tuple(
                requirement
                for requirement in rule.required_regime_states
                if requirement not in declared_states
            )
            if unknown_requirements:
                raise ValueError(
                    "rule required_regime_states must reference declared regime states"
                )


@dataclass
class ContextResearchRegistry:
    _specifications: dict[tuple[str, str], ContextResearchSpec] = field(
        default_factory=dict
    )

    def register(self, specification: ContextResearchSpec) -> None:
        key = (specification.specification_id, specification.definition_version)
        existing = self._specifications.get(key)
        if existing is not None and existing != specification:
            raise ValueError("conflicting context research specification version")
        self._specifications[key] = specification

    def get(self, specification_id: str, definition_version: str) -> ContextResearchSpec:
        try:
            return self._specifications[(specification_id, definition_version)]
        except KeyError as exc:
            raise KeyError("context research specification is not registered") from exc


@dataclass(frozen=True)
class RegimeObservation:
    observation_id: str
    dimension_id: str
    context_protocol_id: str
    raw_value: float
    window_start: datetime
    window_end: datetime
    available_at: datetime
    source_snapshot_id: str

    def __post_init__(self) -> None:
        for name, value in (
            ("observation_id", self.observation_id),
            ("dimension_id", self.dimension_id),
            ("context_protocol_id", self.context_protocol_id),
            ("source_snapshot_id", self.source_snapshot_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not math.isfinite(self.raw_value):
            raise ValueError("regime raw_value must be finite")
        require_aware_timestamp(self.window_start)
        require_aware_timestamp(self.window_end)
        require_aware_timestamp(self.available_at)
        if self.window_end < self.window_start:
            raise ValueError("regime window_end cannot precede window_start")
        if self.available_at < self.window_end:
            raise ValueError("regime available_at cannot precede window_end")


@dataclass(frozen=True)
class ContextFactorSignal:
    admission: FactorAdmission
    normalized_signal_value: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.normalized_signal_value):
            raise ValueError("context factor signal must be finite")


@dataclass(frozen=True)
class RegimeDimensionResult:
    dimension_id: str
    availability: RegimeAvailability
    observation_id: str | None
    raw_value: float | None
    state_id: str | None
    age_days: float | None


@dataclass(frozen=True)
class ContradictionResult:
    rule_id: str
    left_admission_id: str
    right_admission_id: str
    left_signal: float
    right_signal: float
    minimum_absolute_signal: float
    regime_condition_met: bool
    is_contradiction: bool


@dataclass(frozen=True)
class InteractionResult:
    rule_id: str
    left_admission_id: str
    right_admission_id: str
    left_signal: float
    right_signal: float
    state: InteractionState
    interaction_value: float | None


@dataclass(frozen=True)
class ContextResearchResult:
    specification_id: str
    definition_version: str
    horizon: Horizon
    prediction_timestamp: datetime
    status: ContextRunStatus
    regime_results: tuple[RegimeDimensionResult, ...]
    contradiction_results: tuple[ContradictionResult, ...]
    interaction_results: tuple[InteractionResult, ...]
    missing_admission_ids: tuple[str, ...]


def _classify_regime(
    *,
    dimension: RegimeDimensionSpec,
    observation: RegimeObservation | None,
    specification: ContextResearchSpec,
    prediction_timestamp: datetime,
) -> RegimeDimensionResult:
    if observation is None:
        return RegimeDimensionResult(
            dimension_id=dimension.dimension_id,
            availability=RegimeAvailability.MISSING,
            observation_id=None,
            raw_value=None,
            state_id=None,
            age_days=None,
        )
    if observation.dimension_id != dimension.dimension_id:
        raise ValueError("regime observation dimension mismatch")
    if observation.context_protocol_id != specification.context_protocol_id:
        raise ValueError("regime observation protocol mismatch")
    if (
        observation.window_end > prediction_timestamp
        or observation.available_at > prediction_timestamp
    ):
        raise ValueError("future regime evidence cannot enter context research")

    age_days = (prediction_timestamp - observation.window_end).total_seconds() / 86400
    if age_days > dimension.max_age_days:
        return RegimeDimensionResult(
            dimension_id=dimension.dimension_id,
            availability=RegimeAvailability.STALE,
            observation_id=observation.observation_id,
            raw_value=observation.raw_value,
            state_id=None,
            age_days=age_days,
        )

    matching = tuple(
        rule for rule in dimension.state_rules if rule.matches(observation.raw_value)
    )
    if len(matching) != 1:
        raise ValueError("regime observation must match exactly one state rule")
    return RegimeDimensionResult(
        dimension_id=dimension.dimension_id,
        availability=RegimeAvailability.CLASSIFIED,
        observation_id=observation.observation_id,
        raw_value=observation.raw_value,
        state_id=matching[0].state_id,
        age_days=age_days,
    )


def _regime_condition_met(
    requirements: tuple[tuple[str, str], ...],
    regime_states: dict[str, str],
) -> bool:
    return all(regime_states.get(dimension_id) == state_id for dimension_id, state_id in requirements)


def evaluate_context_research(
    *,
    specification: ContextResearchSpec,
    base_alpha_specification: AlphaAggregationSpec,
    base_weights: list[AlphaFactorWeight],
    regime_observations: list[RegimeObservation],
    factor_signals: list[ContextFactorSignal],
    prediction_timestamp: datetime,
) -> ContextResearchResult:
    """Evaluate preregistered context evidence without mutating Alpha."""
    require_aware_timestamp(prediction_timestamp)
    if specification.preregistered_at > prediction_timestamp:
        raise ValueError("context specification was not preregistered by prediction time")
    if specification.horizon is not base_alpha_specification.horizon:
        raise ValueError("context horizon does not match base Alpha")
    if (
        specification.base_alpha_specification_id
        != base_alpha_specification.specification_id
        or specification.base_alpha_definition_version
        != base_alpha_specification.definition_version
    ):
        raise ValueError("context specification references a different base Alpha")

    plan = validate_weight_plan(base_weights, horizon=specification.horizon)
    admissions_by_id = {item.admission.admission_id: item.admission for item in plan}

    observations_by_dimension: dict[str, RegimeObservation] = {}
    for observation in regime_observations:
        if observation.dimension_id in observations_by_dimension:
            raise ValueError("duplicate regime observation for dimension")
        if observation.dimension_id not in {
            item.dimension_id for item in specification.regime_dimensions
        }:
            raise ValueError("regime observation dimension is not declared in specification")
        observations_by_dimension[observation.dimension_id] = observation

    regime_results = tuple(
        _classify_regime(
            dimension=dimension,
            observation=observations_by_dimension.get(dimension.dimension_id),
            specification=specification,
            prediction_timestamp=prediction_timestamp,
        )
        for dimension in specification.regime_dimensions
    )
    if any(
        item.availability is not RegimeAvailability.CLASSIFIED
        for item in regime_results
    ):
        return ContextResearchResult(
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            horizon=specification.horizon,
            prediction_timestamp=prediction_timestamp,
            status=ContextRunStatus.ABSTAIN_INSUFFICIENT_REGIME,
            regime_results=regime_results,
            contradiction_results=(),
            interaction_results=(),
            missing_admission_ids=(),
        )

    regime_states = {
        item.dimension_id: item.state_id
        for item in regime_results
        if item.state_id is not None
    }

    signals_by_admission: dict[str, ContextFactorSignal] = {}
    for signal in factor_signals:
        admission_id = signal.admission.admission_id
        if admission_id in signals_by_admission:
            raise ValueError("duplicate context factor signal")
        expected = admissions_by_id.get(admission_id)
        if expected is None:
            raise ValueError("context factor signal is outside base Alpha plan")
        if expected != signal.admission:
            raise ValueError("context factor signal admission mismatch")
        signals_by_admission[admission_id] = signal

    required_admissions = {
        admission_id
        for rule in (*specification.contradiction_rules, *specification.interaction_rules)
        for admission_id in (rule.left_admission_id, rule.right_admission_id)
    }
    unknown_required = tuple(sorted(required_admissions - set(admissions_by_id)))
    if unknown_required:
        raise ValueError("context rule references admission outside base Alpha plan")
    missing_admissions = tuple(sorted(required_admissions - set(signals_by_admission)))
    if missing_admissions:
        return ContextResearchResult(
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            horizon=specification.horizon,
            prediction_timestamp=prediction_timestamp,
            status=ContextRunStatus.ABSTAIN_INSUFFICIENT_FACTOR_SIGNALS,
            regime_results=regime_results,
            contradiction_results=(),
            interaction_results=(),
            missing_admission_ids=missing_admissions,
        )

    contradiction_results: list[ContradictionResult] = []
    for rule in specification.contradiction_rules:
        left = signals_by_admission[rule.left_admission_id].normalized_signal_value
        right = signals_by_admission[rule.right_admission_id].normalized_signal_value
        regime_condition = _regime_condition_met(
            rule.required_regime_states,
            regime_states,
        )
        contradiction = (
            regime_condition
            and abs(left) >= rule.minimum_absolute_signal
            and abs(right) >= rule.minimum_absolute_signal
            and left * right < 0
        )
        contradiction_results.append(
            ContradictionResult(
                rule_id=rule.rule_id,
                left_admission_id=rule.left_admission_id,
                right_admission_id=rule.right_admission_id,
                left_signal=left,
                right_signal=right,
                minimum_absolute_signal=rule.minimum_absolute_signal,
                regime_condition_met=regime_condition,
                is_contradiction=contradiction,
            )
        )

    interaction_results: list[InteractionResult] = []
    for rule in specification.interaction_rules:
        left = signals_by_admission[rule.left_admission_id].normalized_signal_value
        right = signals_by_admission[rule.right_admission_id].normalized_signal_value
        regime_condition = _regime_condition_met(
            rule.required_regime_states,
            regime_states,
        )
        interaction_results.append(
            InteractionResult(
                rule_id=rule.rule_id,
                left_admission_id=rule.left_admission_id,
                right_admission_id=rule.right_admission_id,
                left_signal=left,
                right_signal=right,
                state=(
                    InteractionState.ACTIVE
                    if regime_condition
                    else InteractionState.INACTIVE_REGIME
                ),
                interaction_value=left * right if regime_condition else None,
            )
        )

    return ContextResearchResult(
        specification_id=specification.specification_id,
        definition_version=specification.definition_version,
        horizon=specification.horizon,
        prediction_timestamp=prediction_timestamp,
        status=ContextRunStatus.EVALUATED,
        regime_results=regime_results,
        contradiction_results=tuple(contradiction_results),
        interaction_results=tuple(interaction_results),
        missing_admission_ids=(),
    )
