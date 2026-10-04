"""Candidate-only ML challenger primitives for Zincir Kıran.

This module is dependency-free by design. It provides a deterministic ridge-style
cross-sectional challenger with explicit point-in-time guards and train-only
standardization. It has no production-promotion path.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .baselines import Horizon
from .pit import require_aware_timestamp


class MLStage(StrEnum):
    CANDIDATE = "CANDIDATE"


@dataclass(frozen=True)
class MLChallengerSpec:
    challenger_id: str
    definition_version: str
    horizon: Horizon
    universe_rule_version: str
    evaluation_target: str
    feature_ids: tuple[str, ...]
    ridge_penalty: float
    preregistered_at: datetime
    random_seed: int
    stage: MLStage = MLStage.CANDIDATE

    def __post_init__(self) -> None:
        for name, value in (
            ("challenger_id", self.challenger_id),
            ("definition_version", self.definition_version),
            ("universe_rule_version", self.universe_rule_version),
            ("evaluation_target", self.evaluation_target),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if self.stage is not MLStage.CANDIDATE:
            raise ValueError("ML challenger is candidate-only")
        if not self.feature_ids:
            raise ValueError("feature_ids cannot be empty")
        if self.feature_ids != tuple(sorted(self.feature_ids)):
            raise ValueError("feature_ids must be sorted")
        if len(set(self.feature_ids)) != len(self.feature_ids):
            raise ValueError("feature_ids must be unique")
        if self.ridge_penalty < 0 or not math.isfinite(self.ridge_penalty):
            raise ValueError("ridge_penalty must be finite and non-negative")


@dataclass(frozen=True)
class MLObservation:
    security_id: str
    observation_at: datetime
    feature_values: tuple[tuple[str, float], ...]
    feature_available_at: tuple[tuple[str, datetime], ...]
    target_value: float | None = None
    target_available_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.security_id.strip():
            raise ValueError("security_id is required")
        require_aware_timestamp(self.observation_at)
        feature_ids = tuple(item[0] for item in self.feature_values)
        if feature_ids != tuple(sorted(feature_ids)) or len(set(feature_ids)) != len(feature_ids):
            raise ValueError("feature_values must be unique and sorted")
        available_ids = tuple(item[0] for item in self.feature_available_at)
        if available_ids != feature_ids:
            raise ValueError("feature availability must exactly match feature values")
        for _, value in self.feature_values:
            if not math.isfinite(value):
                raise ValueError("feature values must be finite; missing is not neutral")
        for _, available_at in self.feature_available_at:
            require_aware_timestamp(available_at)
            if available_at > self.observation_at:
                raise ValueError("future feature evidence is forbidden")
        if self.target_value is not None and not math.isfinite(self.target_value):
            raise ValueError("target_value must be finite when provided")
        if (self.target_value is None) != (self.target_available_at is None):
            raise ValueError("target value and target_available_at must appear together")
        if self.target_available_at is not None:
            require_aware_timestamp(self.target_available_at)


@dataclass(frozen=True)
class TrainedMLChallenger:
    challenger_id: str
    definition_version: str
    feature_ids: tuple[str, ...]
    fit_at: datetime
    training_observations: int
    means: tuple[float, ...]
    scales: tuple[float, ...]
    intercept: float
    coefficients: tuple[float, ...]
    random_seed: int


@dataclass(frozen=True)
class MLPrediction:
    security_id: str
    prediction_at: datetime
    raw_score: float
    challenger_id: str
    definition_version: str
    model_fit_at: datetime


def _row_for_spec(spec: MLChallengerSpec, observation: MLObservation) -> tuple[float, ...]:
    values = dict(observation.feature_values)
    if tuple(sorted(values)) != spec.feature_ids:
        raise ValueError("observation feature set does not match challenger specification")
    return tuple(values[feature_id] for feature_id in spec.feature_ids)


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    augmented = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for pivot in range(n):
        best = max(range(pivot, n), key=lambda idx: abs(augmented[idx][pivot]))
        if abs(augmented[best][pivot]) < 1e-12:
            raise ValueError("training design is singular after regularization")
        augmented[pivot], augmented[best] = augmented[best], augmented[pivot]
        pivot_value = augmented[pivot][pivot]
        augmented[pivot] = [value / pivot_value for value in augmented[pivot]]
        for row_idx in range(n):
            if row_idx == pivot:
                continue
            factor = augmented[row_idx][pivot]
            if factor == 0:
                continue
            augmented[row_idx] = [
                current - factor * reference
                for current, reference in zip(augmented[row_idx], augmented[pivot], strict=True)
            ]
    return [augmented[i][-1] for i in range(n)]


def fit_ridge_challenger(
    specification: MLChallengerSpec,
    observations: list[MLObservation],
    *,
    fit_at: datetime,
) -> TrainedMLChallenger:
    """Fit deterministic ridge regression using only evidence available by fit_at."""
    require_aware_timestamp(fit_at)
    if fit_at <= specification.preregistered_at:
        raise ValueError("fit_at must follow preregistration")
    if not observations:
        raise ValueError("training observations are required")

    rows: list[tuple[float, ...]] = []
    targets: list[float] = []
    for observation in observations:
        if observation.observation_at >= fit_at:
            raise ValueError("training observation must precede fit_at")
        if observation.target_value is None or observation.target_available_at is None:
            raise ValueError("training observation requires an available target")
        if observation.target_available_at > fit_at:
            raise ValueError("future target evidence is forbidden")
        rows.append(_row_for_spec(specification, observation))
        targets.append(observation.target_value)

    feature_count = len(specification.feature_ids)
    means = tuple(
        sum(row[j] for row in rows) / len(rows)
        for j in range(feature_count)
    )
    scales_list: list[float] = []
    for j in range(feature_count):
        variance = sum((row[j] - means[j]) ** 2 for row in rows) / len(rows)
        scale = math.sqrt(variance)
        scales_list.append(scale if scale > 0 else 1.0)
    scales = tuple(scales_list)
    standardized = [
        tuple((row[j] - means[j]) / scales[j] for j in range(feature_count))
        for row in rows
    ]

    # Add an unpenalized intercept.
    dimension = feature_count + 1
    gram = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    rhs = [0.0 for _ in range(dimension)]
    for row, target in zip(standardized, targets, strict=True):
        design = (1.0,) + row
        for i in range(dimension):
            rhs[i] += design[i] * target
            for j in range(dimension):
                gram[i][j] += design[i] * design[j]
    for j in range(1, dimension):
        gram[j][j] += specification.ridge_penalty

    solution = _solve_linear_system(gram, rhs)
    return TrainedMLChallenger(
        challenger_id=specification.challenger_id,
        definition_version=specification.definition_version,
        feature_ids=specification.feature_ids,
        fit_at=fit_at,
        training_observations=len(rows),
        means=means,
        scales=scales,
        intercept=solution[0],
        coefficients=tuple(solution[1:]),
        random_seed=specification.random_seed,
    )


def predict_challenger(
    specification: MLChallengerSpec,
    model: TrainedMLChallenger,
    observations: list[MLObservation],
    *,
    prediction_at: datetime,
) -> tuple[MLPrediction, ...]:
    """Score only observations strictly after the model fit cutoff."""
    require_aware_timestamp(prediction_at)
    if model.challenger_id != specification.challenger_id:
        raise ValueError("model challenger_id does not match specification")
    if model.definition_version != specification.definition_version:
        raise ValueError("model definition_version does not match specification")
    if model.feature_ids != specification.feature_ids:
        raise ValueError("model feature set does not match specification")
    if model.fit_at >= prediction_at:
        raise ValueError("prediction_at must strictly follow model fit_at")

    predictions: list[MLPrediction] = []
    for observation in observations:
        if observation.observation_at != prediction_at:
            raise ValueError("scoring observation timestamp must equal prediction_at")
        row = _row_for_spec(specification, observation)
        standardized = tuple(
            (row[j] - model.means[j]) / model.scales[j]
            for j in range(len(model.feature_ids))
        )
        score = model.intercept + sum(
            coefficient * value
            for coefficient, value in zip(model.coefficients, standardized, strict=True)
        )
        predictions.append(
            MLPrediction(
                security_id=observation.security_id,
                prediction_at=prediction_at,
                raw_score=score,
                challenger_id=model.challenger_id,
                definition_version=model.definition_version,
                model_fit_at=model.fit_at,
            )
        )
    return tuple(sorted(predictions, key=lambda item: item.security_id))
