"""Deterministic execution engine for Interpretable Alpha v1.

This module executes only an explicitly versioned aggregation specification.
It does not choose production weights, normalization, or coverage rules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from math import fsum

from .accounting import ComparabilityDecision
from .alpha_aggregation import AlphaAggregationSpec
from .applicability import Applicability
from .baselines import Horizon
from .interpretable_alpha import AdmissionDecision, FactorAdmission, alpha_field_name


class SignalAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNDECIDED = "UNDECIDED"
    ACCOUNTING_INCOMPATIBLE = "ACCOUNTING_INCOMPATIBLE"


class AlphaExecutionStatus(StrEnum):
    SCORED = "SCORED"
    ABSTAIN_INSUFFICIENT_COVERAGE = "ABSTAIN_INSUFFICIENT_COVERAGE"


SUPPORTED_AGGREGATION_RULES = frozenset({"WEIGHTED_SUM", "WEIGHTED_ABS_MEAN"})
SUPPORTED_COVERAGE_RULES = frozenset({"ABS_WEIGHT_COVERAGE", "FACTOR_COUNT_COVERAGE"})


@dataclass(frozen=True)
class AlphaFactorWeight:
    admission: FactorAdmission
    weight: float

    def __post_init__(self) -> None:
        if self.admission.decision is not AdmissionDecision.ADMITTED:
            raise ValueError("weight plan may contain only ADMITTED factors")
        if not math.isfinite(self.weight) or self.weight == 0:
            raise ValueError("factor weight must be finite and non-zero")


@dataclass(frozen=True)
class AlphaSignalObservation:
    admission: FactorAdmission
    availability: SignalAvailability
    applicability: Applicability
    accounting_comparability: ComparabilityDecision
    raw_signal_value: float | None = None
    normalization_rule_id: str | None = None
    normalized_value: float | None = None

    def __post_init__(self) -> None:
        if self.admission.decision is not AdmissionDecision.ADMITTED:
            raise ValueError("signal observation requires an ADMITTED factor")
        if self.availability is SignalAvailability.AVAILABLE:
            if self.applicability is not Applicability.APPLIES:
                raise ValueError("AVAILABLE signal requires applicability APPLIES")
            if self.accounting_comparability is not ComparabilityDecision.COMPARABLE:
                raise ValueError("AVAILABLE signal requires accounting COMPARABLE")
            if self.raw_signal_value is None or not math.isfinite(self.raw_signal_value):
                raise ValueError("AVAILABLE signal requires finite raw_signal_value")
            if self.normalized_value is None or not math.isfinite(self.normalized_value):
                raise ValueError("AVAILABLE signal requires finite normalized_value")
            if self.normalization_rule_id is None or not self.normalization_rule_id.strip():
                raise ValueError("AVAILABLE signal requires normalization_rule_id")
        else:
            if self.availability is SignalAvailability.NOT_APPLICABLE:
                if self.applicability is not Applicability.DOES_NOT_APPLY:
                    raise ValueError("NOT_APPLICABLE signal requires DOES_NOT_APPLY")
            elif self.availability is SignalAvailability.UNDECIDED:
                if (
                    self.applicability is not Applicability.UNDECIDED
                    and self.accounting_comparability is not ComparabilityDecision.UNDECIDED
                ):
                    raise ValueError("UNDECIDED signal requires an undecided eligibility gate")
            elif (
                self.availability is SignalAvailability.ACCOUNTING_INCOMPATIBLE
                and self.accounting_comparability is not ComparabilityDecision.INCOMPATIBLE
            ):
                raise ValueError(
                    "ACCOUNTING_INCOMPATIBLE signal requires INCOMPATIBLE accounting"
                )
            if (
                self.raw_signal_value is not None
                or self.normalized_value is not None
                or self.normalization_rule_id is not None
            ):
                raise ValueError("unavailable signal cannot carry numeric or normalization values")


@dataclass(frozen=True)
class AlphaContribution:
    admission_id: str
    factor_id: str
    factor_definition_version: str
    decorrelation_run_id: str
    decorrelation_component_no: int
    raw_signal_value: float
    normalization_rule_id: str
    applicability: Applicability
    accounting_comparability: ComparabilityDecision
    normalized_value: float
    weight: float
    weighted_contribution: float


@dataclass(frozen=True)
class AlphaUnavailableInput:
    admission_id: str
    factor_id: str
    factor_definition_version: str
    availability: SignalAvailability
    applicability: Applicability
    accounting_comparability: ComparabilityDecision
    absolute_weight: float


@dataclass(frozen=True)
class InterpretableAlphaResult:
    security_id: str
    horizon: Horizon
    alpha_field: str
    specification_id: str
    definition_version: str
    status: AlphaExecutionStatus
    alpha_value: float | None
    coverage: float
    planned_factor_count: int
    available_factor_count: int
    planned_absolute_weight: float
    available_absolute_weight: float
    contributions: tuple[AlphaContribution, ...]
    unavailable_inputs: tuple[AlphaUnavailableInput, ...]


def _spec_parameters(specification: AlphaAggregationSpec) -> dict[str, str]:
    return dict(specification.parameters)


def _minimum_coverage(specification: AlphaAggregationSpec) -> float:
    parameters = _spec_parameters(specification)
    try:
        value = float(parameters["minimum_coverage"])
    except KeyError as exc:
        raise ValueError("aggregation specification requires minimum_coverage") from exc
    except ValueError as exc:
        raise ValueError("minimum_coverage must be numeric") from exc
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("minimum_coverage must be in [0, 1]")
    return value


def validate_weight_plan(
    weights: list[AlphaFactorWeight],
    *,
    horizon: Horizon,
) -> tuple[AlphaFactorWeight, ...]:
    if not weights:
        raise ValueError("alpha weight plan cannot be empty")

    seen_admissions: set[str] = set()
    seen_factors: set[tuple[str, str]] = set()
    seen_components: set[tuple[str, int]] = set()
    validated: list[AlphaFactorWeight] = []

    for item in weights:
        admission = item.admission
        if admission.horizon is not horizon:
            raise ValueError("weight-plan admission horizon does not match alpha horizon")
        if admission.admission_id in seen_admissions:
            raise ValueError("duplicate admission in alpha weight plan")
        seen_admissions.add(admission.admission_id)

        factor_key = (admission.factor_id, admission.factor_definition_version)
        if factor_key in seen_factors:
            raise ValueError("duplicate factor definition in alpha weight plan")
        seen_factors.add(factor_key)

        component_key = (
            admission.decorrelation_run_id,
            admission.decorrelation_component_no,
        )
        if component_key in seen_components:
            raise ValueError("alpha weight plan contains duplicate de-correlation vote")
        seen_components.add(component_key)
        validated.append(item)

    return tuple(
        sorted(
            validated,
            key=lambda item: (
                item.admission.factor_id,
                item.admission.factor_definition_version,
                item.admission.admission_id,
            ),
        )
    )


def execute_interpretable_alpha(
    *,
    security_id: str,
    specification: AlphaAggregationSpec,
    weights: list[AlphaFactorWeight],
    observations: list[AlphaSignalObservation],
) -> InterpretableAlphaResult:
    """Execute one deterministic Alpha v1 score or explicit abstention."""
    if not security_id.strip():
        raise ValueError("security_id is required")
    if specification.aggregation_rule_id not in SUPPORTED_AGGREGATION_RULES:
        raise ValueError("unsupported aggregation_rule_id")
    if specification.coverage_rule_id not in SUPPORTED_COVERAGE_RULES:
        raise ValueError("unsupported coverage_rule_id")

    horizon = specification.horizon
    minimum_coverage = _minimum_coverage(specification)
    plan = validate_weight_plan(weights, horizon=horizon)
    plan_by_admission = {item.admission.admission_id: item for item in plan}

    if len(observations) != len(plan):
        raise ValueError("every planned admission requires one explicit signal observation")

    observations_by_admission: dict[str, AlphaSignalObservation] = {}
    for observation in observations:
        admission_id = observation.admission.admission_id
        if admission_id in observations_by_admission:
            raise ValueError("duplicate signal observation for admission")
        planned = plan_by_admission.get(admission_id)
        if planned is None:
            raise ValueError("signal observation is not part of the weight plan")
        if planned.admission != observation.admission:
            raise ValueError("signal observation admission does not match weight plan")
        observations_by_admission[admission_id] = observation

    if set(observations_by_admission) != set(plan_by_admission):
        raise ValueError("signal observations do not exactly match the weight plan")

    planned_absolute_weight = fsum(abs(item.weight) for item in plan)
    available_items = [
        item
        for item in plan
        if observations_by_admission[item.admission.admission_id].availability
        is SignalAvailability.AVAILABLE
    ]
    available_absolute_weight = fsum(abs(item.weight) for item in available_items)

    if specification.coverage_rule_id == "ABS_WEIGHT_COVERAGE":
        coverage = available_absolute_weight / planned_absolute_weight
    else:
        coverage = len(available_items) / len(plan)

    contributions: list[AlphaContribution] = []
    unavailable: list[AlphaUnavailableInput] = []
    for planned in plan:
        admission = planned.admission
        observation = observations_by_admission[admission.admission_id]
        if observation.availability is not SignalAvailability.AVAILABLE:
            unavailable.append(
                AlphaUnavailableInput(
                    admission_id=admission.admission_id,
                    factor_id=admission.factor_id,
                    factor_definition_version=admission.factor_definition_version,
                    availability=observation.availability,
                    applicability=observation.applicability,
                    accounting_comparability=observation.accounting_comparability,
                    absolute_weight=abs(planned.weight),
                )
            )
            continue

        assert observation.normalization_rule_id is not None
        assert observation.raw_signal_value is not None
        assert observation.normalized_value is not None
        if observation.normalization_rule_id != specification.normalization_rule_id:
            raise ValueError("signal normalization does not match aggregation specification")

        weighted_contribution = observation.normalized_value * planned.weight
        contributions.append(
            AlphaContribution(
                admission_id=admission.admission_id,
                factor_id=admission.factor_id,
                factor_definition_version=admission.factor_definition_version,
                decorrelation_run_id=admission.decorrelation_run_id,
                decorrelation_component_no=admission.decorrelation_component_no,
                raw_signal_value=observation.raw_signal_value,
                normalization_rule_id=observation.normalization_rule_id,
                applicability=observation.applicability,
                accounting_comparability=observation.accounting_comparability,
                normalized_value=observation.normalized_value,
                weight=planned.weight,
                weighted_contribution=weighted_contribution,
            )
        )

    contributions_tuple = tuple(contributions)
    unavailable_tuple = tuple(unavailable)
    if coverage < minimum_coverage:
        return InterpretableAlphaResult(
            security_id=security_id,
            horizon=horizon,
            alpha_field=alpha_field_name(horizon),
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            status=AlphaExecutionStatus.ABSTAIN_INSUFFICIENT_COVERAGE,
            alpha_value=None,
            coverage=coverage,
            planned_factor_count=len(plan),
            available_factor_count=len(available_items),
            planned_absolute_weight=planned_absolute_weight,
            available_absolute_weight=available_absolute_weight,
            contributions=contributions_tuple,
            unavailable_inputs=unavailable_tuple,
        )

    numerator = fsum(item.weighted_contribution for item in contributions_tuple)
    if specification.aggregation_rule_id == "WEIGHTED_SUM":
        alpha_value = numerator
    else:
        if available_absolute_weight == 0:
            raise ValueError("cannot aggregate with zero available absolute weight")
        alpha_value = numerator / available_absolute_weight

    return InterpretableAlphaResult(
        security_id=security_id,
        horizon=horizon,
        alpha_field=alpha_field_name(horizon),
        specification_id=specification.specification_id,
        definition_version=specification.definition_version,
        status=AlphaExecutionStatus.SCORED,
        alpha_value=alpha_value,
        coverage=coverage,
        planned_factor_count=len(plan),
        available_factor_count=len(available_items),
        planned_absolute_weight=planned_absolute_weight,
        available_absolute_weight=available_absolute_weight,
        contributions=contributions_tuple,
        unavailable_inputs=unavailable_tuple,
    )
