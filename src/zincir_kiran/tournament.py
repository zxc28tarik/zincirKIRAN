"""Walk-forward champion/challenger tournament primitives for Zincir Kıran.

The tournament records OOS evidence. It never auto-promotes a challenger.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from statistics import fmean, stdev

from .baselines import Horizon
from .factor_lab import benjamini_hochberg_qvalues
from .pit import require_aware_timestamp


class TournamentStage(StrEnum):
    CANDIDATE = "CANDIDATE"


class ContenderRole(StrEnum):
    CHAMPION = "CHAMPION"
    CHALLENGER = "CHALLENGER"


class MetricDirection(StrEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"


class TournamentDecision(StrEnum):
    RETAIN_CHAMPION_REVIEW_REQUIRED = "RETAIN_CHAMPION_REVIEW_REQUIRED"


@dataclass(frozen=True)
class TournamentContender:
    contender_id: str
    role: ContenderRole
    artifact_kind: str
    artifact_specification_id: str
    artifact_definition_version: str
    rationale: str

    def __post_init__(self) -> None:
        for name, value in (
            ("contender_id", self.contender_id),
            ("artifact_kind", self.artifact_kind),
            ("artifact_specification_id", self.artifact_specification_id),
            ("artifact_definition_version", self.artifact_definition_version),
            ("rationale", self.rationale),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class WalkForwardFold:
    fold_id: str
    train_start: date
    train_end: date
    validation_start: date
    validation_end: date

    def __post_init__(self) -> None:
        if not self.fold_id.strip():
            raise ValueError("fold_id is required")
        if self.train_start > self.train_end:
            raise ValueError("train_start cannot follow train_end")
        if self.train_end >= self.validation_start:
            raise ValueError("walk-forward fold requires train_end < validation_start")
        if self.validation_start > self.validation_end:
            raise ValueError("validation_start cannot follow validation_end")

    @property
    def purge_gap_days(self) -> int:
        return (self.validation_start - self.train_end).days - 1


@dataclass(frozen=True)
class TournamentMetricSpec:
    metric_id: str
    direction: MetricDirection
    required: bool
    requires_cost_model: bool = False

    def __post_init__(self) -> None:
        if not self.metric_id.strip():
            raise ValueError("metric_id is required")


@dataclass(frozen=True)
class TournamentSpec:
    tournament_id: str
    definition_version: str
    horizon: Horizon
    universe_rule_version: str
    evaluation_target: str
    hypothesis: str
    success_criteria: str
    preregistered_at: datetime
    purge_days: int
    embargo_days: int
    multiple_testing_method: str
    primary_metric_id: str
    contenders: tuple[TournamentContender, ...]
    folds: tuple[WalkForwardFold, ...]
    metrics: tuple[TournamentMetricSpec, ...]
    stage: TournamentStage = TournamentStage.CANDIDATE

    def __post_init__(self) -> None:
        for name, value in (
            ("tournament_id", self.tournament_id),
            ("definition_version", self.definition_version),
            ("universe_rule_version", self.universe_rule_version),
            ("evaluation_target", self.evaluation_target),
            ("hypothesis", self.hypothesis),
            ("success_criteria", self.success_criteria),
            ("multiple_testing_method", self.multiple_testing_method),
            ("primary_metric_id", self.primary_metric_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if self.stage is not TournamentStage.CANDIDATE:
            raise ValueError("tournament implementation is candidate-only")
        if self.purge_days < 0 or self.embargo_days < 0:
            raise ValueError("purge_days and embargo_days cannot be negative")
        if self.multiple_testing_method != "BENJAMINI_HOCHBERG":
            raise ValueError("unsupported multiple_testing_method")
        if len(self.contenders) < 2:
            raise ValueError("tournament requires at least two contenders")
        if len(self.folds) < 2:
            raise ValueError("tournament requires at least two walk-forward folds")
        if not self.metrics:
            raise ValueError("tournament requires metric specifications")

        contender_ids = tuple(item.contender_id for item in self.contenders)
        if contender_ids != tuple(sorted(contender_ids)) or len(set(contender_ids)) != len(
            contender_ids
        ):
            raise ValueError("contenders must be unique and sorted by contender_id")
        champions = [
            item for item in self.contenders if item.role is ContenderRole.CHAMPION
        ]
        if len(champions) != 1:
            raise ValueError("tournament requires exactly one CHAMPION")

        fold_ids = tuple(item.fold_id for item in self.folds)
        if len(set(fold_ids)) != len(fold_ids):
            raise ValueError("fold_ids must be unique")
        if self.folds != tuple(sorted(self.folds, key=lambda item: item.validation_start)):
            raise ValueError("folds must be sorted by validation_start")

        previous_validation_end: date | None = None
        for fold in self.folds:
            if fold.purge_gap_days < self.purge_days:
                raise ValueError("walk-forward fold violates purge_days")
            if previous_validation_end is not None:
                if fold.validation_start <= previous_validation_end:
                    raise ValueError("validation folds cannot overlap")
                embargo_gap = (fold.validation_start - previous_validation_end).days - 1
                if embargo_gap < self.embargo_days:
                    raise ValueError("walk-forward folds violate embargo_days")
            previous_validation_end = fold.validation_end

        metric_ids = tuple(item.metric_id for item in self.metrics)
        if metric_ids != tuple(sorted(metric_ids)) or len(set(metric_ids)) != len(metric_ids):
            raise ValueError("metrics must be unique and sorted by metric_id")
        if self.primary_metric_id not in set(metric_ids):
            raise ValueError("primary_metric_id must reference a declared metric")


@dataclass
class TournamentRegistry:
    _specifications: dict[tuple[str, str], TournamentSpec] = field(default_factory=dict)

    def register(self, specification: TournamentSpec) -> None:
        key = (specification.tournament_id, specification.definition_version)
        existing = self._specifications.get(key)
        if existing is not None and existing != specification:
            raise ValueError("conflicting tournament specification version")
        self._specifications[key] = specification


@dataclass(frozen=True)
class FoldMetricObservation:
    contender_id: str
    fold_id: str
    metric_id: str
    value: float | None
    sample_size: int
    cost_model_id: str | None = None

    def __post_init__(self) -> None:
        if not self.contender_id.strip() or not self.fold_id.strip() or not self.metric_id.strip():
            raise ValueError("contender_id, fold_id and metric_id are required")
        if self.sample_size < 0:
            raise ValueError("sample_size cannot be negative")
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError("fold metric value must be finite when provided")


@dataclass(frozen=True)
class AggregateMetric:
    contender_id: str
    metric_id: str
    valid_folds: int
    total_folds: int
    mean_value: float | None
    dispersion: float | None


@dataclass(frozen=True)
class PairedChampionDifference:
    challenger_id: str
    metric_id: str
    paired_folds: int
    mean_difference_vs_champion: float | None


@dataclass(frozen=True)
class MultipleTestingEvidence:
    contender_id: str
    metric_id: str
    pvalue: float
    qvalue: float


@dataclass(frozen=True)
class TournamentOutcome:
    champion_id: str
    decision: TournamentDecision
    automatic_promotion: bool
    review_required: bool
    primary_metric_id: str
    aggregates: tuple[AggregateMetric, ...]
    paired_differences: tuple[PairedChampionDifference, ...]
    multiple_testing: tuple[MultipleTestingEvidence, ...]


def validate_fold_metrics(
    specification: TournamentSpec,
    observations: list[FoldMetricObservation],
) -> tuple[FoldMetricObservation, ...]:
    contender_ids = {item.contender_id for item in specification.contenders}
    fold_ids = {item.fold_id for item in specification.folds}
    metric_specs = {item.metric_id: item for item in specification.metrics}
    seen: set[tuple[str, str, str]] = set()
    validated: list[FoldMetricObservation] = []

    for item in observations:
        key = (item.contender_id, item.fold_id, item.metric_id)
        if key in seen:
            raise ValueError("duplicate fold metric observation")
        seen.add(key)
        if item.contender_id not in contender_ids:
            raise ValueError("fold metric contender is not preregistered")
        if item.fold_id not in fold_ids:
            raise ValueError("fold metric fold is not preregistered")
        metric = metric_specs.get(item.metric_id)
        if metric is None:
            raise ValueError("fold metric is not preregistered")
        if metric.requires_cost_model and item.value is not None:
            if item.cost_model_id is None or not item.cost_model_id.strip():
                raise ValueError("net/cost-aware metric requires cost_model_id")
        validated.append(item)

    return tuple(sorted(validated, key=lambda item: (
        item.contender_id, item.fold_id, item.metric_id
    )))


def aggregate_fold_metrics(
    specification: TournamentSpec,
    observations: list[FoldMetricObservation],
) -> tuple[AggregateMetric, ...]:
    validated = validate_fold_metrics(specification, observations)
    values_by_key: dict[tuple[str, str], list[float]] = {
        (contender.contender_id, metric.metric_id): []
        for contender in specification.contenders
        for metric in specification.metrics
    }
    for item in validated:
        if item.value is not None:
            values_by_key[(item.contender_id, item.metric_id)].append(item.value)

    aggregates: list[AggregateMetric] = []
    total_folds = len(specification.folds)
    for contender in specification.contenders:
        for metric in specification.metrics:
            values = values_by_key[(contender.contender_id, metric.metric_id)]
            mean_value = fmean(values) if values else None
            dispersion = stdev(values) if len(values) >= 2 else None
            aggregates.append(
                AggregateMetric(
                    contender_id=contender.contender_id,
                    metric_id=metric.metric_id,
                    valid_folds=len(values),
                    total_folds=total_folds,
                    mean_value=mean_value,
                    dispersion=dispersion,
                )
            )
    return tuple(aggregates)


def paired_champion_differences(
    specification: TournamentSpec,
    observations: list[FoldMetricObservation],
) -> tuple[PairedChampionDifference, ...]:
    validated = validate_fold_metrics(specification, observations)
    champion = next(
        item for item in specification.contenders if item.role is ContenderRole.CHAMPION
    )
    metric_specs = {item.metric_id: item for item in specification.metrics}
    by_key = {
        (item.contender_id, item.fold_id, item.metric_id): item.value
        for item in validated
    }

    results: list[PairedChampionDifference] = []
    for contender in specification.contenders:
        if contender.role is ContenderRole.CHAMPION:
            continue
        for metric_id, metric_spec in sorted(metric_specs.items()):
            differences: list[float] = []
            for fold in specification.folds:
                champion_value = by_key.get((champion.contender_id, fold.fold_id, metric_id))
                challenger_value = by_key.get((contender.contender_id, fold.fold_id, metric_id))
                if champion_value is None or challenger_value is None:
                    continue
                raw_difference = challenger_value - champion_value
                if metric_spec.direction is MetricDirection.LOWER_IS_BETTER:
                    raw_difference = -raw_difference
                differences.append(raw_difference)
            results.append(
                PairedChampionDifference(
                    challenger_id=contender.contender_id,
                    metric_id=metric_id,
                    paired_folds=len(differences),
                    mean_difference_vs_champion=(
                        fmean(differences) if differences else None
                    ),
                )
            )
    return tuple(results)


def multiple_testing_evidence(
    specification: TournamentSpec,
    pvalues: dict[tuple[str, str], float],
) -> tuple[MultipleTestingEvidence, ...]:
    challenger_ids = {
        item.contender_id
        for item in specification.contenders
        if item.role is ContenderRole.CHALLENGER
    }
    metric_ids = {item.metric_id for item in specification.metrics}
    flattened: dict[str, float] = {}
    original_keys: dict[str, tuple[str, str]] = {}

    for (contender_id, metric_id), pvalue in pvalues.items():
        if contender_id not in challenger_ids:
            raise ValueError("pvalue contender must be a preregistered CHALLENGER")
        if metric_id not in metric_ids:
            raise ValueError("pvalue metric is not preregistered")
        key = f"{contender_id}::{metric_id}"
        flattened[key] = pvalue
        original_keys[key] = (contender_id, metric_id)

    qvalues = benjamini_hochberg_qvalues(flattened)
    return tuple(
        MultipleTestingEvidence(
            contender_id=original_keys[key][0],
            metric_id=original_keys[key][1],
            pvalue=flattened[key],
            qvalue=qvalues[key],
        )
        for key in sorted(flattened)
    )


def build_tournament_outcome(
    *,
    specification: TournamentSpec,
    observations: list[FoldMetricObservation],
    pvalues: dict[tuple[str, str], float],
) -> TournamentOutcome:
    champion = next(
        item for item in specification.contenders if item.role is ContenderRole.CHAMPION
    )
    return TournamentOutcome(
        champion_id=champion.contender_id,
        decision=TournamentDecision.RETAIN_CHAMPION_REVIEW_REQUIRED,
        automatic_promotion=False,
        review_required=True,
        primary_metric_id=specification.primary_metric_id,
        aggregates=aggregate_fold_metrics(specification, observations),
        paired_differences=paired_champion_differences(specification, observations),
        multiple_testing=multiple_testing_evidence(specification, pvalues),
    )
