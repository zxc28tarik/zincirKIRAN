"""Statistical primitives and experiment gates for the Factor Laboratory."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from statistics import fmean, stdev

from .baselines import Horizon
from .factor_library import ExpectedDirection
from .pit import require_aware_timestamp


@dataclass(frozen=True)
class FactorObservation:
    security_id: str
    factor_value: float | None
    forward_excess_return: float | None
    liquidity_tier: str | None = None


@dataclass(frozen=True)
class PreparedSample:
    security_ids: tuple[str, ...]
    factor_values: tuple[float, ...]
    forward_excess_returns: tuple[float, ...]
    total_observations: int

    @property
    def used_observations(self) -> int:
        return len(self.security_ids)

    @property
    def coverage(self) -> float:
        if self.total_observations == 0:
            return 0.0
        return self.used_observations / self.total_observations


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def prepare_sample(observations: list[FactorObservation]) -> PreparedSample:
    """Exclude unusable rows with explicit coverage loss; never neutral-fill them."""
    usable = [
        item
        for item in observations
        if _finite(item.factor_value) and _finite(item.forward_excess_return)
    ]
    usable.sort(key=lambda item: item.security_id)
    return PreparedSample(
        security_ids=tuple(item.security_id for item in usable),
        factor_values=tuple(float(item.factor_value) for item in usable),  # type: ignore[arg-type]
        forward_excess_returns=tuple(
            float(item.forward_excess_return) for item in usable  # type: ignore[arg-type]
        ),
        total_observations=len(observations),
    )


def average_ranks(values: tuple[float, ...]) -> tuple[float, ...]:
    """Return deterministic one-based average ranks with proper tie handling."""
    indexed = sorted(enumerate(values), key=lambda pair: (pair[1], pair[0]))
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = ((index + 1) + end) / 2
        for position in range(index, end):
            ranks[indexed[position][0]] = average_rank
        index = end
    return tuple(ranks)


def _pearson(left: tuple[float, ...], right: tuple[float, ...]) -> float | None:
    if len(left) != len(right):
        raise ValueError("vectors must have equal length")
    if len(left) < 2:
        return None
    left_mean = fmean(left)
    right_mean = fmean(right)
    left_centered = tuple(value - left_mean for value in left)
    right_centered = tuple(value - right_mean for value in right)
    denominator = math.sqrt(
        sum(value * value for value in left_centered)
        * sum(value * value for value in right_centered)
    )
    if denominator == 0:
        return None
    numerator = sum(a * b for a, b in zip(left_centered, right_centered, strict=True))
    return numerator / denominator


def spearman_ic(factor_values: tuple[float, ...], forward_returns: tuple[float, ...]) -> float | None:
    """Calculate tie-aware cross-sectional Spearman information coefficient."""
    if len(factor_values) != len(forward_returns):
        raise ValueError("factor and return vectors must have equal length")
    return _pearson(average_ranks(factor_values), average_ranks(forward_returns))


@dataclass(frozen=True)
class DatedIC:
    as_of: date
    value: float | None


@dataclass(frozen=True)
class ICSummary:
    valid_periods: int
    total_periods: int
    mean_ic: float | None
    icir: float | None


def summarize_ic_series(series: list[DatedIC]) -> ICSummary:
    """Summarize dated ICs without converting invalid periods to zero."""
    valid = [item.value for item in series if item.value is not None and math.isfinite(item.value)]
    mean_ic = fmean(valid) if valid else None
    icir = None
    if len(valid) >= 2:
        dispersion = stdev(valid)
        if dispersion != 0:
            icir = mean_ic / dispersion if mean_ic is not None else None
    return ICSummary(
        valid_periods=len(valid),
        total_periods=len(series),
        mean_ic=mean_ic,
        icir=icir,
    )


def quantile_assignments(
    sample: PreparedSample,
    *,
    quantile_count: int,
) -> tuple[int, ...]:
    """Assign equal factor values to the same deterministic rank-based quantile."""
    if quantile_count < 2:
        raise ValueError("quantile_count must be at least 2")
    if sample.used_observations < quantile_count:
        raise ValueError("not enough usable observations for requested quantiles")
    ranks = average_ranks(sample.factor_values)
    size = sample.used_observations
    return tuple(
        min(quantile_count - 1, int((rank - 1) * quantile_count / size))
        for rank in ranks
    )


def quantile_mean_returns(
    sample: PreparedSample,
    assignments: tuple[int, ...],
    *,
    quantile_count: int,
) -> tuple[float | None, ...]:
    if len(assignments) != sample.used_observations:
        raise ValueError("assignment length must match sample")
    buckets: list[list[float]] = [[] for _ in range(quantile_count)]
    for bucket, value in zip(assignments, sample.forward_excess_returns, strict=True):
        if bucket < 0 or bucket >= quantile_count:
            raise ValueError("invalid quantile assignment")
        buckets[bucket].append(value)
    return tuple(fmean(bucket) if bucket else None for bucket in buckets)


def quantile_monotonicity(quantile_returns: tuple[float | None, ...]) -> float | None:
    """Spearman relation between quantile order and realized mean excess return."""
    pairs = [
        (float(index), value)
        for index, value in enumerate(quantile_returns)
        if value is not None and math.isfinite(value)
    ]
    if len(pairs) < 2:
        return None
    indexes = tuple(pair[0] for pair in pairs)
    returns = tuple(float(pair[1]) for pair in pairs)
    return spearman_ic(indexes, returns)


@dataclass(frozen=True)
class LongLegMetrics:
    top_vs_market: float | None
    bottom_vs_market: float | None
    top_minus_bottom: float | None


def long_leg_metrics(quantile_returns: tuple[float | None, ...]) -> LongLegMetrics:
    if len(quantile_returns) < 2:
        raise ValueError("at least two quantiles are required")
    bottom = quantile_returns[0]
    top = quantile_returns[-1]
    spread = None if top is None or bottom is None else top - bottom
    return LongLegMetrics(
        top_vs_market=top,
        bottom_vs_market=bottom,
        top_minus_bottom=spread,
    )


@dataclass(frozen=True)
class CrossSectionMetrics:
    sample_size: int
    total_observations: int
    coverage: float
    ic: float | None
    quantile_returns: tuple[float | None, ...]
    monotonicity: float | None
    long_leg: LongLegMetrics


def evaluate_cross_section(
    observations: list[FactorObservation],
    *,
    quantile_count: int,
) -> CrossSectionMetrics:
    sample = prepare_sample(observations)
    assignments = quantile_assignments(sample, quantile_count=quantile_count)
    returns = quantile_mean_returns(sample, assignments, quantile_count=quantile_count)
    return CrossSectionMetrics(
        sample_size=sample.used_observations,
        total_observations=sample.total_observations,
        coverage=sample.coverage,
        ic=spearman_ic(sample.factor_values, sample.forward_excess_returns),
        quantile_returns=returns,
        monotonicity=quantile_monotonicity(returns),
        long_leg=long_leg_metrics(returns),
    )


def liquidity_tier_metrics(
    observations: list[FactorObservation],
    *,
    quantile_count: int,
) -> dict[str, CrossSectionMetrics]:
    """Evaluate each explicit liquidity tier separately; unknown tier is not guessed."""
    tiers = sorted({item.liquidity_tier for item in observations if item.liquidity_tier})
    return {
        tier: evaluate_cross_section(
            [item for item in observations if item.liquidity_tier == tier],
            quantile_count=quantile_count,
        )
        for tier in tiers
    }


def equal_weight_turnover(previous: tuple[str, ...], current: tuple[str, ...]) -> float:
    """Half-L1 turnover for equal-weight portfolios with possibly different sizes."""
    if not previous or not current:
        raise ValueError("turnover requires non-empty portfolios")
    if len(set(previous)) != len(previous) or len(set(current)) != len(current):
        raise ValueError("portfolio members must be unique")
    previous_weight = 1 / len(previous)
    current_weight = 1 / len(current)
    union = set(previous) | set(current)
    l1 = sum(
        abs(
            (previous_weight if security_id in previous else 0.0)
            - (current_weight if security_id in current else 0.0)
        )
        for security_id in union
    )
    return 0.5 * l1


def cost_adjusted_return(
    gross_return: float,
    *,
    turnover: float,
    cost_per_unit_turnover: float,
) -> float:
    """Apply an explicit linear cost assumption; no hidden default cost exists."""
    if not 0 <= turnover <= 1:
        raise ValueError("turnover must be between 0 and 1")
    if cost_per_unit_turnover < 0:
        raise ValueError("cost_per_unit_turnover cannot be negative")
    return gross_return - turnover * cost_per_unit_turnover


def benjamini_hochberg_qvalues(pvalues: dict[str, float]) -> dict[str, float]:
    """Return Benjamini-Hochberg adjusted q-values for multiple-testing control."""
    if not pvalues:
        return {}
    for factor_id, value in pvalues.items():
        if not 0 <= value <= 1:
            raise ValueError(f"invalid p-value for {factor_id}")

    ordered = sorted(pvalues.items(), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 1.0
    for reverse_index in range(count - 1, -1, -1):
        factor_id, value = ordered[reverse_index]
        rank = reverse_index + 1
        running = min(running, value * count / rank)
        adjusted[factor_id] = min(1.0, running)
    return adjusted


@dataclass(frozen=True)
class FactorExperimentSpec:
    experiment_id: str
    factor_id: str
    factor_definition_version: str
    horizon: Horizon
    data_snapshot_id: str
    universe_rule_version: str
    quantile_count: int
    cost_model_id: str
    hypothesis: str
    expected_direction: ExpectedDirection
    preregistered_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("experiment_id", self.experiment_id),
            ("factor_id", self.factor_id),
            ("factor_definition_version", self.factor_definition_version),
            ("data_snapshot_id", self.data_snapshot_id),
            ("universe_rule_version", self.universe_rule_version),
            ("cost_model_id", self.cost_model_id),
            ("hypothesis", self.hypothesis),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.quantile_count < 2:
            raise ValueError("quantile_count must be at least 2")
        require_aware_timestamp(self.preregistered_at)


@dataclass
class FactorExperimentRegistry:
    _specs: dict[str, FactorExperimentSpec] = field(default_factory=dict)

    def register(self, spec: FactorExperimentSpec) -> None:
        existing = self._specs.get(spec.experiment_id)
        if existing is not None and existing != spec:
            raise ValueError("conflicting experiment pre-registration")
        self._specs[spec.experiment_id] = spec

    def get(self, experiment_id: str) -> FactorExperimentSpec:
        try:
            return self._specs[experiment_id]
        except KeyError as exc:
            raise KeyError("experiment is not pre-registered") from exc
