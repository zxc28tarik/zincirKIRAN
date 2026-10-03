"""PIT-safe candidate dynamic evidence weighting for Interpretable Alpha.

The engine resolves research-candidate factor weights from evidence available at
the prediction timestamp. It never selects production parameters on its own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from math import fsum

from .alpha_aggregation import AlphaAggregationSpec
from .alpha_engine import AlphaFactorWeight, validate_weight_plan
from .baselines import Horizon
from .interpretable_alpha import FactorAdmission
from .pit import require_aware_timestamp


class DynamicWeightingStage(StrEnum):
    CANDIDATE = "CANDIDATE"


class GrossExposurePolicy(StrEnum):
    NONE = "NONE"
    PRESERVE_BASE_ABS_SUM = "PRESERVE_BASE_ABS_SUM"


class DynamicWeightPlanStatus(StrEnum):
    RESOLVED = "RESOLVED"
    ABSTAIN_INSUFFICIENT_EVIDENCE = "ABSTAIN_INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class EvidenceMetricRule:
    metric_id: str
    normalization_rule_id: str
    bad_reference: float
    good_reference: float

    def __post_init__(self) -> None:
        if not self.metric_id.strip():
            raise ValueError("metric_id is required")
        if not self.normalization_rule_id.strip():
            raise ValueError("normalization_rule_id is required")
        if not math.isfinite(self.bad_reference) or not math.isfinite(self.good_reference):
            raise ValueError("evidence normalization references must be finite")
        if self.bad_reference == self.good_reference:
            raise ValueError("bad_reference and good_reference must differ")

    def normalize(self, raw_value: float) -> float:
        if not math.isfinite(raw_value):
            raise ValueError("evidence raw_value must be finite")
        scaled = (raw_value - self.bad_reference) / (
            self.good_reference - self.bad_reference
        )
        return min(1.0, max(0.0, scaled))


@dataclass(frozen=True)
class EvidenceTerm:
    rule: EvidenceMetricRule
    coefficient: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.coefficient) or self.coefficient <= 0:
            raise ValueError("evidence coefficient must be finite and positive")


@dataclass(frozen=True)
class DynamicWeightingSpec:
    specification_id: str
    definition_version: str
    horizon: Horizon
    base_alpha_specification_id: str
    base_alpha_definition_version: str
    minimum_metric_coverage: float
    max_evidence_age_days: int
    multiplier_floor: float
    multiplier_ceiling: float
    gross_exposure_policy: GrossExposurePolicy
    terms: tuple[EvidenceTerm, ...]
    stage: DynamicWeightingStage = DynamicWeightingStage.CANDIDATE

    def __post_init__(self) -> None:
        for name, value in (
            ("specification_id", self.specification_id),
            ("definition_version", self.definition_version),
            ("base_alpha_specification_id", self.base_alpha_specification_id),
            ("base_alpha_definition_version", self.base_alpha_definition_version),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.stage is not DynamicWeightingStage.CANDIDATE:
            raise ValueError("dynamic weighting implementation is candidate-only")
        if not 0 <= self.minimum_metric_coverage <= 1:
            raise ValueError("minimum_metric_coverage must be in [0, 1]")
        if self.max_evidence_age_days < 0:
            raise ValueError("max_evidence_age_days cannot be negative")
        if not math.isfinite(self.multiplier_floor) or self.multiplier_floor <= 0:
            raise ValueError("multiplier_floor must be finite and positive")
        if (
            not math.isfinite(self.multiplier_ceiling)
            or self.multiplier_ceiling < self.multiplier_floor
        ):
            raise ValueError("multiplier_ceiling must be finite and >= multiplier_floor")
        if not self.terms:
            raise ValueError("dynamic weighting specification requires evidence terms")

        ordered_keys = tuple(
            (term.rule.metric_id, term.rule.normalization_rule_id) for term in self.terms
        )
        if ordered_keys != tuple(sorted(ordered_keys)) or len(set(ordered_keys)) != len(ordered_keys):
            raise ValueError("evidence terms must be unique and sorted")
        metric_ids = tuple(term.rule.metric_id for term in self.terms)
        if len(set(metric_ids)) != len(metric_ids):
            raise ValueError("each metric_id may appear only once in a weighting spec")


@dataclass
class DynamicWeightingRegistry:
    _specifications: dict[tuple[str, str], DynamicWeightingSpec] = field(
        default_factory=dict
    )

    def register(self, specification: DynamicWeightingSpec) -> None:
        key = (specification.specification_id, specification.definition_version)
        existing = self._specifications.get(key)
        if existing is not None and existing != specification:
            raise ValueError("conflicting dynamic weighting specification version")
        self._specifications[key] = specification

    def get(self, specification_id: str, definition_version: str) -> DynamicWeightingSpec:
        try:
            return self._specifications[(specification_id, definition_version)]
        except KeyError as exc:
            raise KeyError("dynamic weighting specification is not registered") from exc


@dataclass(frozen=True)
class EvidenceMetricObservation:
    metric_id: str
    raw_value: float

    def __post_init__(self) -> None:
        if not self.metric_id.strip():
            raise ValueError("metric_id is required")
        if not math.isfinite(self.raw_value):
            raise ValueError("evidence raw_value must be finite")


@dataclass(frozen=True)
class FactorEvidenceSnapshot:
    snapshot_id: str
    admission: FactorAdmission
    evidence_protocol_id: str
    window_start: datetime
    window_end: datetime
    available_at: datetime
    metrics: tuple[EvidenceMetricObservation, ...]

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id is required")
        if not self.evidence_protocol_id.strip():
            raise ValueError("evidence_protocol_id is required")
        require_aware_timestamp(self.window_start)
        require_aware_timestamp(self.window_end)
        require_aware_timestamp(self.available_at)
        if self.window_end < self.window_start:
            raise ValueError("evidence window_end cannot precede window_start")
        if self.available_at < self.window_end:
            raise ValueError("evidence available_at cannot precede window_end")
        metric_ids = tuple(metric.metric_id for metric in self.metrics)
        if metric_ids != tuple(sorted(metric_ids)) or len(set(metric_ids)) != len(metric_ids):
            raise ValueError("evidence metrics must be unique and sorted")


@dataclass(frozen=True)
class EvidenceMetricContribution:
    metric_id: str
    normalization_rule_id: str
    raw_value: float
    normalized_quality: float
    coefficient: float
    weighted_quality_contribution: float


@dataclass(frozen=True)
class DynamicFactorResolution:
    admission_id: str
    factor_id: str
    base_weight: float
    evidence_snapshot_id: str
    evidence_coverage: float
    evidence_score: float
    multiplier: float
    preliminary_weight: float
    final_weight: float | None
    metric_contributions: tuple[EvidenceMetricContribution, ...]
    missing_metric_ids: tuple[str, ...]


@dataclass(frozen=True)
class DynamicWeightPlanResult:
    specification_id: str
    definition_version: str
    base_alpha_specification_id: str
    base_alpha_definition_version: str
    horizon: Horizon
    prediction_timestamp: datetime
    status: DynamicWeightPlanStatus
    base_gross_exposure: float
    preliminary_gross_exposure: float | None
    resolved_gross_exposure: float | None
    gross_rescale_factor: float | None
    factor_resolutions: tuple[DynamicFactorResolution, ...]
    insufficient_admission_ids: tuple[str, ...]


def _resolve_snapshot(
    *,
    snapshot: FactorEvidenceSnapshot,
    base_weight: float,
    specification: DynamicWeightingSpec,
    prediction_timestamp: datetime,
) -> DynamicFactorResolution | None:
    if snapshot.available_at > prediction_timestamp or snapshot.window_end > prediction_timestamp:
        raise ValueError("future evidence cannot enter dynamic weighting")
    age_days = (prediction_timestamp - snapshot.window_end).total_seconds() / 86400
    if age_days > specification.max_evidence_age_days:
        return None

    metric_map = {metric.metric_id: metric for metric in snapshot.metrics}
    total_coefficient = fsum(term.coefficient for term in specification.terms)
    available_terms: list[tuple[EvidenceTerm, EvidenceMetricObservation]] = []
    missing: list[str] = []
    for term in specification.terms:
        metric = metric_map.get(term.rule.metric_id)
        if metric is None:
            missing.append(term.rule.metric_id)
            continue
        available_terms.append((term, metric))

    available_coefficient = fsum(term.coefficient for term, _ in available_terms)
    coverage = available_coefficient / total_coefficient
    if coverage < specification.minimum_metric_coverage or not available_terms:
        return None

    contributions: list[EvidenceMetricContribution] = []
    numerator_terms: list[float] = []
    for term, metric in available_terms:
        quality = term.rule.normalize(metric.raw_value)
        weighted = quality * term.coefficient
        numerator_terms.append(weighted)
        contributions.append(
            EvidenceMetricContribution(
                metric_id=term.rule.metric_id,
                normalization_rule_id=term.rule.normalization_rule_id,
                raw_value=metric.raw_value,
                normalized_quality=quality,
                coefficient=term.coefficient,
                weighted_quality_contribution=weighted,
            )
        )

    evidence_score = fsum(numerator_terms) / available_coefficient
    multiplier = specification.multiplier_floor + evidence_score * (
        specification.multiplier_ceiling - specification.multiplier_floor
    )
    preliminary_weight = base_weight * multiplier
    if preliminary_weight == 0 or math.copysign(1.0, preliminary_weight) != math.copysign(
        1.0, base_weight
    ):
        raise ValueError("dynamic multiplier cannot remove or flip base-weight sign")

    return DynamicFactorResolution(
        admission_id=snapshot.admission.admission_id,
        factor_id=snapshot.admission.factor_id,
        base_weight=base_weight,
        evidence_snapshot_id=snapshot.snapshot_id,
        evidence_coverage=coverage,
        evidence_score=evidence_score,
        multiplier=multiplier,
        preliminary_weight=preliminary_weight,
        final_weight=None,
        metric_contributions=tuple(contributions),
        missing_metric_ids=tuple(missing),
    )


def resolve_dynamic_evidence_weights(
    *,
    specification: DynamicWeightingSpec,
    base_alpha_specification: AlphaAggregationSpec,
    base_weights: list[AlphaFactorWeight],
    evidence_snapshots: list[FactorEvidenceSnapshot],
    prediction_timestamp: datetime,
) -> DynamicWeightPlanResult:
    """Resolve candidate dynamic weights from PIT-safe evidence or abstain as a plan."""
    require_aware_timestamp(prediction_timestamp)
    if specification.horizon is not base_alpha_specification.horizon:
        raise ValueError("dynamic weighting horizon does not match base alpha specification")
    if (
        specification.base_alpha_specification_id
        != base_alpha_specification.specification_id
        or specification.base_alpha_definition_version
        != base_alpha_specification.definition_version
    ):
        raise ValueError("dynamic weighting specification references a different base alpha spec")

    plan = validate_weight_plan(base_weights, horizon=specification.horizon)
    plan_by_admission = {item.admission.admission_id: item for item in plan}
    snapshots_by_admission: dict[str, FactorEvidenceSnapshot] = {}
    for snapshot in evidence_snapshots:
        admission_id = snapshot.admission.admission_id
        if admission_id in snapshots_by_admission:
            raise ValueError("duplicate evidence snapshot for admission")
        planned = plan_by_admission.get(admission_id)
        if planned is None:
            raise ValueError("evidence snapshot is not part of the base weight plan")
        if snapshot.admission != planned.admission:
            raise ValueError("evidence snapshot admission does not match base weight plan")
        snapshots_by_admission[admission_id] = snapshot

    resolutions: list[DynamicFactorResolution] = []
    insufficient: list[str] = []
    for planned in plan:
        admission_id = planned.admission.admission_id
        snapshot = snapshots_by_admission.get(admission_id)
        if snapshot is None:
            insufficient.append(admission_id)
            continue
        resolution = _resolve_snapshot(
            snapshot=snapshot,
            base_weight=planned.weight,
            specification=specification,
            prediction_timestamp=prediction_timestamp,
        )
        if resolution is None:
            insufficient.append(admission_id)
        else:
            resolutions.append(resolution)

    base_gross = fsum(abs(item.weight) for item in plan)
    ordered_resolutions = tuple(sorted(resolutions, key=lambda item: item.admission_id))
    insufficient_tuple = tuple(sorted(insufficient))
    if insufficient_tuple:
        return DynamicWeightPlanResult(
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            base_alpha_specification_id=specification.base_alpha_specification_id,
            base_alpha_definition_version=specification.base_alpha_definition_version,
            horizon=specification.horizon,
            prediction_timestamp=prediction_timestamp,
            status=DynamicWeightPlanStatus.ABSTAIN_INSUFFICIENT_EVIDENCE,
            base_gross_exposure=base_gross,
            preliminary_gross_exposure=None,
            resolved_gross_exposure=None,
            gross_rescale_factor=None,
            factor_resolutions=ordered_resolutions,
            insufficient_admission_ids=insufficient_tuple,
        )

    preliminary_gross = fsum(abs(item.preliminary_weight) for item in ordered_resolutions)
    if preliminary_gross <= 0:
        raise ValueError("dynamic plan preliminary gross exposure must be positive")
    if specification.gross_exposure_policy is GrossExposurePolicy.PRESERVE_BASE_ABS_SUM:
        scale = base_gross / preliminary_gross
    else:
        scale = 1.0

    finalized = tuple(
        DynamicFactorResolution(
            admission_id=item.admission_id,
            factor_id=item.factor_id,
            base_weight=item.base_weight,
            evidence_snapshot_id=item.evidence_snapshot_id,
            evidence_coverage=item.evidence_coverage,
            evidence_score=item.evidence_score,
            multiplier=item.multiplier,
            preliminary_weight=item.preliminary_weight,
            final_weight=item.preliminary_weight * scale,
            metric_contributions=item.metric_contributions,
            missing_metric_ids=item.missing_metric_ids,
        )
        for item in ordered_resolutions
    )
    resolved_gross = fsum(abs(item.final_weight or 0.0) for item in finalized)

    return DynamicWeightPlanResult(
        specification_id=specification.specification_id,
        definition_version=specification.definition_version,
        base_alpha_specification_id=specification.base_alpha_specification_id,
        base_alpha_definition_version=specification.base_alpha_definition_version,
        horizon=specification.horizon,
        prediction_timestamp=prediction_timestamp,
        status=DynamicWeightPlanStatus.RESOLVED,
        base_gross_exposure=base_gross,
        preliminary_gross_exposure=preliminary_gross,
        resolved_gross_exposure=resolved_gross,
        gross_rescale_factor=scale,
        factor_resolutions=finalized,
        insufficient_admission_ids=(),
    )


def resolved_alpha_weights(
    result: DynamicWeightPlanResult,
    *,
    admissions: tuple[FactorAdmission, ...],
) -> tuple[AlphaFactorWeight, ...]:
    """Convert only a fully resolved candidate plan into AlphaFactorWeight objects."""
    if result.status is not DynamicWeightPlanStatus.RESOLVED:
        raise ValueError("cannot use an abstained dynamic weight plan")
    admissions_by_id = {admission.admission_id: admission for admission in admissions}
    if len(admissions_by_id) != len(admissions):
        raise ValueError("duplicate admission supplied for resolved weights")

    weights: list[AlphaFactorWeight] = []
    for resolution in result.factor_resolutions:
        admission = admissions_by_id.get(resolution.admission_id)
        if admission is None:
            raise ValueError("resolved factor admission is missing")
        if resolution.final_weight is None:
            raise ValueError("resolved factor is missing final_weight")
        weights.append(AlphaFactorWeight(admission=admission, weight=resolution.final_weight))
    return validate_weight_plan(weights, horizon=result.horizon)
