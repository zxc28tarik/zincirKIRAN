"""Experimental Factor-Lab run orchestration over existing statistical primitives."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from statistics import fmean

from .baselines import Horizon
from .experimental_factors import FactorDirection
from .factor_lab import (
    CrossSectionMetrics,
    DatedIC,
    FactorObservation,
    ICSummary,
    evaluate_cross_section,
    prepare_sample,
    summarize_ic_series,
)
from .pit import require_aware_timestamp

AUTHORITY = "EXPERIMENTAL_VERSION_RISK"


@dataclass(frozen=True)
class DatedFactorCrossSection:
    as_of: date
    observations: tuple[FactorObservation, ...]

    def __post_init__(self) -> None:
        ids = [item.security_id for item in self.observations]
        if len(ids) != len(set(ids)):
            raise ValueError("security_id must be unique within one cross-section")


@dataclass(frozen=True)
class ExperimentalFactorLabRunSpec:
    run_id: str
    dataset_id: str
    factor_id: str
    factor_definition_version: str
    horizon: Horizon
    direction: FactorDirection
    quantile_count: int
    cost_model_id: str
    preregistered_at: datetime
    authority: str = AUTHORITY

    def __post_init__(self) -> None:
        for name, value in (
            ("run_id", self.run_id),
            ("dataset_id", self.dataset_id),
            ("factor_id", self.factor_id),
            ("factor_definition_version", self.factor_definition_version),
            ("cost_model_id", self.cost_model_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if self.quantile_count < 2:
            raise ValueError("quantile_count must be at least 2")
        if self.authority != AUTHORITY:
            raise ValueError("experimental Factor-Lab run authority is fixed")


@dataclass(frozen=True)
class PeriodFactorLabResult:
    as_of: date
    metrics: CrossSectionMetrics | None
    unavailable_reason: str | None

    def __post_init__(self) -> None:
        if (self.metrics is None) != (self.unavailable_reason is not None):
            raise ValueError("unavailable period must carry exactly one reason")


@dataclass(frozen=True)
class LiquidityTierSummary:
    tier: str
    total_periods: int
    valid_periods: int
    mean_ic: float | None
    icir: float | None
    mean_top_vs_market: float | None
    mean_top_minus_bottom: float | None


@dataclass(frozen=True)
class ExperimentalFactorLabSummary:
    run_id: str
    dataset_id: str
    factor_id: str
    horizon: Horizon
    authority: str
    periods: tuple[PeriodFactorLabResult, ...]
    ic_summary: ICSummary
    mean_coverage: float
    mean_top_vs_market: float | None
    mean_top_minus_bottom: float | None
    liquidity_tiers: tuple[LiquidityTierSummary, ...]


def _normalize_direction(
    observations: tuple[FactorObservation, ...],
    direction: FactorDirection,
) -> list[FactorObservation]:
    sign = -1.0 if direction is FactorDirection.LOWER_IS_BETTER else 1.0
    return [
        FactorObservation(
            security_id=item.security_id,
            factor_value=(
                None
                if item.factor_value is None
                else sign * item.factor_value
            ),
            forward_excess_return=item.forward_excess_return,
            liquidity_tier=item.liquidity_tier,
        )
        for item in observations
    ]


def _mean_finite(values: list[float | None]) -> float | None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    return fmean(finite) if finite else None


def _evaluate_period(
    section: DatedFactorCrossSection,
    *,
    direction: FactorDirection,
    quantile_count: int,
) -> PeriodFactorLabResult:
    normalized = _normalize_direction(section.observations, direction)
    sample = prepare_sample(normalized)
    if sample.used_observations < quantile_count:
        return PeriodFactorLabResult(
            as_of=section.as_of,
            metrics=None,
            unavailable_reason="INSUFFICIENT_USABLE_OBSERVATIONS",
        )
    return PeriodFactorLabResult(
        as_of=section.as_of,
        metrics=evaluate_cross_section(normalized, quantile_count=quantile_count),
        unavailable_reason=None,
    )


def _summarize_liquidity_tier(
    tier: str,
    sections: tuple[DatedFactorCrossSection, ...],
    *,
    direction: FactorDirection,
    quantile_count: int,
) -> LiquidityTierSummary:
    dated_ics: list[DatedIC] = []
    tops: list[float | None] = []
    spreads: list[float | None] = []
    valid = 0
    for section in sections:
        subset = tuple(
            item for item in section.observations if item.liquidity_tier == tier
        )
        result = _evaluate_period(
            DatedFactorCrossSection(section.as_of, subset),
            direction=direction,
            quantile_count=quantile_count,
        )
        if result.metrics is None:
            dated_ics.append(DatedIC(section.as_of, None))
            continue
        valid += 1
        dated_ics.append(DatedIC(section.as_of, result.metrics.ic))
        tops.append(result.metrics.long_leg.top_vs_market)
        spreads.append(result.metrics.long_leg.top_minus_bottom)
    ic = summarize_ic_series(dated_ics)
    return LiquidityTierSummary(
        tier=tier,
        total_periods=len(sections),
        valid_periods=valid,
        mean_ic=ic.mean_ic,
        icir=ic.icir,
        mean_top_vs_market=_mean_finite(tops),
        mean_top_minus_bottom=_mean_finite(spreads),
    )


def run_experimental_factor_lab(
    specification: ExperimentalFactorLabRunSpec,
    sections: tuple[DatedFactorCrossSection, ...],
    *,
    executed_at: datetime,
) -> ExperimentalFactorLabSummary:
    require_aware_timestamp(executed_at)
    if executed_at <= specification.preregistered_at:
        raise ValueError("Factor-Lab execution must follow preregistration")
    if not sections:
        raise ValueError("at least one dated cross-section is required")
    ordered = tuple(sorted(sections, key=lambda item: item.as_of))
    if ordered != sections:
        raise ValueError("cross-sections must be chronologically sorted")
    if len({item.as_of for item in sections}) != len(sections):
        raise ValueError("cross-section dates must be unique")

    periods = tuple(
        _evaluate_period(
            section,
            direction=specification.direction,
            quantile_count=specification.quantile_count,
        )
        for section in sections
    )
    dated_ics = [
        DatedIC(
            result.as_of,
            None if result.metrics is None else result.metrics.ic,
        )
        for result in periods
    ]
    ic_summary = summarize_ic_series(dated_ics)
    coverages = [
        0.0 if result.metrics is None else result.metrics.coverage
        for result in periods
    ]
    tops = [
        None if result.metrics is None else result.metrics.long_leg.top_vs_market
        for result in periods
    ]
    spreads = [
        None if result.metrics is None else result.metrics.long_leg.top_minus_bottom
        for result in periods
    ]

    tiers = tuple(
        sorted(
            {
                observation.liquidity_tier
                for section in sections
                for observation in section.observations
                if observation.liquidity_tier
            }
        )
    )
    liquidity = tuple(
        _summarize_liquidity_tier(
            tier,
            sections,
            direction=specification.direction,
            quantile_count=specification.quantile_count,
        )
        for tier in tiers
    )

    return ExperimentalFactorLabSummary(
        run_id=specification.run_id,
        dataset_id=specification.dataset_id,
        factor_id=specification.factor_id,
        horizon=specification.horizon,
        authority=AUTHORITY,
        periods=periods,
        ic_summary=ic_summary,
        mean_coverage=fmean(coverages),
        mean_top_vs_market=_mean_finite(tops),
        mean_top_minus_bottom=_mean_finite(spreads),
        liquidity_tiers=liquidity,
    )


def require_authoritative_promotion(_: ExperimentalFactorLabSummary) -> None:
    raise ValueError(
        "experimental Factor-Lab result cannot authorize LAB_VALIDATED, champion, "
        "shadow, or production promotion"
    )
