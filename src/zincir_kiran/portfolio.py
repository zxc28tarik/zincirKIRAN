"""Deterministic long-only Portfolio Engine for Zincir Kıran.

The Portfolio Engine consumes Alpha + Confidence outputs and never mutates them.
Production parameters remain explicit versioned specification data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from math import fsum

from .alpha_engine import AlphaExecutionStatus, InterpretableAlphaResult
from .baselines import Horizon
from .confidence import ConfidenceDecision, ConfidenceResult
from .pit import require_aware_timestamp


class PortfolioStage(StrEnum):
    CANDIDATE = "CANDIDATE"


class SelectionRule(StrEnum):
    TOP_ALPHA = "TOP_ALPHA"


class SizingRule(StrEnum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    POSITIVE_ALPHA_PROPORTIONAL = "POSITIVE_ALPHA_PROPORTIONAL"


class PortfolioRunStatus(StrEnum):
    CONSTRUCTED = "CONSTRUCTED"
    INFEASIBLE_INSUFFICIENT_ELIGIBLE = "INFEASIBLE_INSUFFICIENT_ELIGIBLE"
    INFEASIBLE_CONSTRAINTS = "INFEASIBLE_CONSTRAINTS"
    INFEASIBLE_LIQUIDITY = "INFEASIBLE_LIQUIDITY"
    INFEASIBLE_TURNOVER = "INFEASIBLE_TURNOVER"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class PortfolioSpec:
    specification_id: str
    definition_version: str
    horizon: Horizon
    base_alpha_specification_id: str
    base_alpha_definition_version: str
    confidence_specification_id: str
    confidence_definition_version: str
    universe_rule_version: str
    hypothesis: str
    success_criteria: str
    preregistered_at: datetime
    selection_rule: SelectionRule
    sizing_rule: SizingRule
    rebalance_rule_id: str
    target_position_count: int
    minimum_position_count: int
    minimum_alpha_value: float
    target_invested_weight: float
    max_single_name_weight: float
    max_sector_weight: float
    max_participation_rate: float
    execution_days: int
    max_liquidity_age_days: int
    maximum_one_way_turnover: float
    stage: PortfolioStage = PortfolioStage.CANDIDATE

    def __post_init__(self) -> None:
        for name, value in (
            ("specification_id", self.specification_id),
            ("definition_version", self.definition_version),
            ("base_alpha_specification_id", self.base_alpha_specification_id),
            ("base_alpha_definition_version", self.base_alpha_definition_version),
            ("confidence_specification_id", self.confidence_specification_id),
            ("confidence_definition_version", self.confidence_definition_version),
            ("universe_rule_version", self.universe_rule_version),
            ("hypothesis", self.hypothesis),
            ("success_criteria", self.success_criteria),
            ("rebalance_rule_id", self.rebalance_rule_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.preregistered_at)
        if self.stage is not PortfolioStage.CANDIDATE:
            raise ValueError("portfolio implementation is candidate-only")
        if self.target_position_count < 1:
            raise ValueError("target_position_count must be at least 1")
        if not 1 <= self.minimum_position_count <= self.target_position_count:
            raise ValueError("minimum_position_count must be in [1, target_position_count]")
        if not math.isfinite(self.minimum_alpha_value):
            raise ValueError("minimum_alpha_value must be finite")
        if not 0 < self.target_invested_weight <= 1:
            raise ValueError("target_invested_weight must be in (0, 1]")
        if not 0 < self.max_single_name_weight <= 1:
            raise ValueError("max_single_name_weight must be in (0, 1]")
        if not 0 < self.max_sector_weight <= 1:
            raise ValueError("max_sector_weight must be in (0, 1]")
        if not 0 < self.max_participation_rate <= 1:
            raise ValueError("max_participation_rate must be in (0, 1]")
        if self.execution_days < 1:
            raise ValueError("execution_days must be at least 1")
        if self.max_liquidity_age_days < 0:
            raise ValueError("max_liquidity_age_days cannot be negative")
        if (
            not math.isfinite(self.maximum_one_way_turnover)
            or self.maximum_one_way_turnover < 0
        ):
            raise ValueError("maximum_one_way_turnover must be finite and non-negative")


@dataclass
class PortfolioSpecRegistry:
    _specifications: dict[tuple[str, str], PortfolioSpec] = field(default_factory=dict)

    def register(self, specification: PortfolioSpec) -> None:
        key = (specification.specification_id, specification.definition_version)
        existing = self._specifications.get(key)
        if existing is not None and existing != specification:
            raise ValueError("conflicting portfolio specification version")
        self._specifications[key] = specification

    def get(self, specification_id: str, definition_version: str) -> PortfolioSpec:
        try:
            return self._specifications[(specification_id, definition_version)]
        except KeyError as exc:
            raise KeyError("portfolio specification is not registered") from exc


@dataclass(frozen=True)
class ExecutionEvidence:
    security_id: str
    window_end: datetime
    available_at: datetime
    average_daily_notional: float
    commission_bps: float
    half_spread_bps: float
    slippage_bps: float
    market_impact_bps: float
    source_reference: str

    def __post_init__(self) -> None:
        if not self.security_id.strip():
            raise ValueError("security_id is required")
        if not self.source_reference.strip():
            raise ValueError("source_reference is required")
        require_aware_timestamp(self.window_end)
        require_aware_timestamp(self.available_at)
        if self.available_at < self.window_end:
            raise ValueError("execution evidence available_at cannot precede window_end")
        if (
            not math.isfinite(self.average_daily_notional)
            or self.average_daily_notional <= 0
        ):
            raise ValueError("average_daily_notional must be finite and positive")
        for name, value in (
            ("commission_bps", self.commission_bps),
            ("half_spread_bps", self.half_spread_bps),
            ("slippage_bps", self.slippage_bps),
            ("market_impact_bps", self.market_impact_bps),
        ):
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class PortfolioCandidate:
    security_id: str
    sector_id: str
    alpha_result: InterpretableAlphaResult
    confidence_result: ConfidenceResult

    def __post_init__(self) -> None:
        if not self.security_id.strip():
            raise ValueError("security_id is required")
        if not self.sector_id.strip():
            raise ValueError("sector_id is required")
        if self.alpha_result.security_id != self.security_id:
            raise ValueError("candidate Alpha security mismatch")
        if self.confidence_result.security_id != self.security_id:
            raise ValueError("candidate Confidence security mismatch")
        if (
            self.confidence_result.source_alpha_specification_id
            != self.alpha_result.specification_id
            or self.confidence_result.source_alpha_definition_version
            != self.alpha_result.definition_version
            or self.confidence_result.source_alpha_value != self.alpha_result.alpha_value
        ):
            raise ValueError("candidate Confidence does not preserve source Alpha")


@dataclass(frozen=True)
class CurrentHolding:
    security_id: str
    weight: float

    def __post_init__(self) -> None:
        if not self.security_id.strip():
            raise ValueError("security_id is required")
        if not math.isfinite(self.weight) or self.weight < 0:
            raise ValueError("current holding weight must be finite and non-negative")


@dataclass(frozen=True)
class TargetPosition:
    security_id: str
    sector_id: str
    alpha_value: float
    confidence_score: float | None
    rank: int
    target_weight: float


@dataclass(frozen=True)
class RebalanceOrder:
    security_id: str
    side: OrderSide
    current_weight: float
    target_weight: float
    delta_weight: float
    trade_notional: float
    max_trade_notional: float | None
    commission_cost: float
    spread_cost: float
    slippage_cost: float
    market_impact_cost: float
    total_cost: float


@dataclass(frozen=True)
class PortfolioResult:
    specification_id: str
    definition_version: str
    horizon: Horizon
    prediction_timestamp: datetime
    portfolio_notional: float
    status: PortfolioRunStatus
    target_positions: tuple[TargetPosition, ...]
    cash_weight: float
    one_way_turnover: float
    gross_turnover: float
    total_estimated_cost: float
    orders: tuple[RebalanceOrder, ...]
    infeasibility_reasons: tuple[str, ...]


def _eligible_candidates(
    candidates: list[PortfolioCandidate],
    specification: PortfolioSpec,
) -> tuple[PortfolioCandidate, ...]:
    seen: set[str] = set()
    eligible: list[PortfolioCandidate] = []
    for candidate in candidates:
        if candidate.security_id in seen:
            raise ValueError("duplicate portfolio candidate security")
        seen.add(candidate.security_id)
        alpha = candidate.alpha_result
        confidence = candidate.confidence_result
        if alpha.horizon is not specification.horizon:
            raise ValueError("candidate Alpha horizon mismatch")
        if confidence.horizon is not specification.horizon:
            raise ValueError("candidate Confidence horizon mismatch")
        if (
            alpha.specification_id != specification.base_alpha_specification_id
            or alpha.definition_version != specification.base_alpha_definition_version
        ):
            raise ValueError("candidate Alpha specification mismatch")
        if (
            confidence.specification_id != specification.confidence_specification_id
            or confidence.definition_version != specification.confidence_definition_version
        ):
            raise ValueError("candidate Confidence specification mismatch")
        if alpha.status is not AlphaExecutionStatus.SCORED:
            continue
        if confidence.decision is not ConfidenceDecision.SIGNAL_ELIGIBLE:
            continue
        if confidence.confidence_score is None or not math.isfinite(
            confidence.confidence_score
        ):
            raise ValueError("eligible portfolio candidate requires finite Confidence")
        if alpha.alpha_value is None or not math.isfinite(alpha.alpha_value):
            raise ValueError("eligible portfolio candidate requires finite Alpha")
        if alpha.alpha_value < specification.minimum_alpha_value:
            continue
        eligible.append(candidate)

    return tuple(
        sorted(
            eligible,
            key=lambda item: (
                -(item.alpha_result.alpha_value or 0.0),
                item.security_id,
            ),
        )
    )


def _raw_sizing_weights(
    selected: tuple[PortfolioCandidate, ...],
    specification: PortfolioSpec,
) -> dict[str, float]:
    if specification.sizing_rule is SizingRule.EQUAL_WEIGHT:
        return {item.security_id: 1.0 for item in selected}

    positive_alpha = {
        item.security_id: max(0.0, item.alpha_result.alpha_value or 0.0)
        for item in selected
    }
    if any(value <= 0 for value in positive_alpha.values()):
        raise ValueError(
            "POSITIVE_ALPHA_PROPORTIONAL requires strictly positive selected Alpha values"
        )
    return positive_alpha


def _allocate_with_caps(
    *,
    selected: tuple[PortfolioCandidate, ...],
    raw_weights: dict[str, float],
    specification: PortfolioSpec,
) -> dict[str, float] | None:
    """Normalize the declared sizing primitive, then validate hard caps.

    Caps never trigger hidden redistribution. A raw sizing plan that violates a
    name or sector cap is explicitly infeasible.
    """
    raw_total = fsum(raw_weights.values())
    if raw_total <= 0:
        return None

    assigned = {
        security_id: (
            specification.target_invested_weight
            * raw_weight
            / raw_total
        )
        for security_id, raw_weight in raw_weights.items()
    }
    if any(
        weight > specification.max_single_name_weight + 1e-12
        for weight in assigned.values()
    ):
        return None

    sector_weights: dict[str, float] = {}
    for candidate in selected:
        sector_weights[candidate.sector_id] = (
            sector_weights.get(candidate.sector_id, 0.0)
            + assigned[candidate.security_id]
        )
    if any(
        weight > specification.max_sector_weight + 1e-12
        for weight in sector_weights.values()
    ):
        return None
    return assigned


def construct_portfolio(
    *,
    specification: PortfolioSpec,
    candidates: list[PortfolioCandidate],
    current_holdings: list[CurrentHolding],
    execution_evidence: list[ExecutionEvidence],
    prediction_timestamp: datetime,
    portfolio_notional: float,
) -> PortfolioResult:
    """Construct a deterministic long-only target and rebalance plan."""
    require_aware_timestamp(prediction_timestamp)
    if specification.preregistered_at > prediction_timestamp:
        raise ValueError("portfolio specification was not preregistered by prediction time")
    if not math.isfinite(portfolio_notional) or portfolio_notional <= 0:
        raise ValueError("portfolio_notional must be finite and positive")

    current_by_id: dict[str, float] = {}
    for holding in current_holdings:
        if holding.security_id in current_by_id:
            raise ValueError("duplicate current holding security")
        current_by_id[holding.security_id] = holding.weight
    if fsum(current_by_id.values()) > 1 + 1e-12:
        raise ValueError("current holding weights cannot exceed 1")

    evidence_by_id: dict[str, ExecutionEvidence] = {}
    for evidence in execution_evidence:
        if evidence.security_id in evidence_by_id:
            raise ValueError("duplicate execution evidence security")
        if (
            evidence.window_end > prediction_timestamp
            or evidence.available_at > prediction_timestamp
        ):
            raise ValueError("future execution evidence cannot enter portfolio construction")
        evidence_by_id[evidence.security_id] = evidence

    eligible = _eligible_candidates(candidates, specification)
    if len(eligible) < specification.minimum_position_count:
        return PortfolioResult(
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            horizon=specification.horizon,
            prediction_timestamp=prediction_timestamp,
            portfolio_notional=portfolio_notional,
            status=PortfolioRunStatus.INFEASIBLE_INSUFFICIENT_ELIGIBLE,
            target_positions=(),
            cash_weight=1.0,
            one_way_turnover=0.0,
            gross_turnover=0.0,
            total_estimated_cost=0.0,
            orders=(),
            infeasibility_reasons=("INSUFFICIENT_ELIGIBLE_SECURITIES",),
        )

    selected = eligible[: specification.target_position_count]
    if len(selected) < specification.minimum_position_count:
        raise AssertionError("selected portfolio unexpectedly below minimum_position_count")

    raw_weights = _raw_sizing_weights(selected, specification)
    allocated = _allocate_with_caps(
        selected=selected,
        raw_weights=raw_weights,
        specification=specification,
    )
    if allocated is None:
        return PortfolioResult(
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            horizon=specification.horizon,
            prediction_timestamp=prediction_timestamp,
            portfolio_notional=portfolio_notional,
            status=PortfolioRunStatus.INFEASIBLE_CONSTRAINTS,
            target_positions=(),
            cash_weight=1.0,
            one_way_turnover=0.0,
            gross_turnover=0.0,
            total_estimated_cost=0.0,
            orders=(),
            infeasibility_reasons=("WEIGHT_OR_SECTOR_CAPS_INFEASIBLE",),
        )

    target_positions = tuple(
        TargetPosition(
            security_id=item.security_id,
            sector_id=item.sector_id,
            alpha_value=item.alpha_result.alpha_value or 0.0,
            confidence_score=item.confidence_result.confidence_score,
            rank=index + 1,
            target_weight=allocated[item.security_id],
        )
        for index, item in enumerate(selected)
    )
    target_by_id = {item.security_id: item.target_weight for item in target_positions}
    all_security_ids = sorted(set(current_by_id) | set(target_by_id))

    orders: list[RebalanceOrder] = []
    liquidity_failures: list[str] = []
    absolute_deltas: list[float] = []

    for security_id in all_security_ids:
        current_weight = current_by_id.get(security_id, 0.0)
        target_weight = target_by_id.get(security_id, 0.0)
        delta = target_weight - current_weight
        absolute_deltas.append(abs(delta))

        if abs(delta) <= 1e-15:
            orders.append(
                RebalanceOrder(
                    security_id=security_id,
                    side=OrderSide.HOLD,
                    current_weight=current_weight,
                    target_weight=target_weight,
                    delta_weight=0.0,
                    trade_notional=0.0,
                    max_trade_notional=None,
                    commission_cost=0.0,
                    spread_cost=0.0,
                    slippage_cost=0.0,
                    market_impact_cost=0.0,
                    total_cost=0.0,
                )
            )
            continue

        evidence = evidence_by_id.get(security_id)
        if evidence is None:
            liquidity_failures.append(f"MISSING_EXECUTION_EVIDENCE:{security_id}")
            continue
        age_days = (prediction_timestamp - evidence.window_end).total_seconds() / 86400
        if age_days > specification.max_liquidity_age_days:
            liquidity_failures.append(f"STALE_EXECUTION_EVIDENCE:{security_id}")
            continue

        trade_notional = abs(delta) * portfolio_notional
        max_trade_notional = (
            evidence.average_daily_notional
            * specification.max_participation_rate
            * specification.execution_days
        )
        if trade_notional > max_trade_notional + 1e-9:
            liquidity_failures.append(f"CAPACITY_EXCEEDED:{security_id}")
            continue

        commission_cost = trade_notional * evidence.commission_bps / 10000
        spread_cost = trade_notional * evidence.half_spread_bps / 10000
        slippage_cost = trade_notional * evidence.slippage_bps / 10000
        market_impact_cost = trade_notional * evidence.market_impact_bps / 10000
        total_cost = (
            commission_cost
            + spread_cost
            + slippage_cost
            + market_impact_cost
        )
        orders.append(
            RebalanceOrder(
                security_id=security_id,
                side=OrderSide.BUY if delta > 0 else OrderSide.SELL,
                current_weight=current_weight,
                target_weight=target_weight,
                delta_weight=delta,
                trade_notional=trade_notional,
                max_trade_notional=max_trade_notional,
                commission_cost=commission_cost,
                spread_cost=spread_cost,
                slippage_cost=slippage_cost,
                market_impact_cost=market_impact_cost,
                total_cost=total_cost,
            )
        )

    gross_turnover = fsum(absolute_deltas)
    one_way_turnover = gross_turnover / 2
    if liquidity_failures:
        return PortfolioResult(
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            horizon=specification.horizon,
            prediction_timestamp=prediction_timestamp,
            portfolio_notional=portfolio_notional,
            status=PortfolioRunStatus.INFEASIBLE_LIQUIDITY,
            target_positions=target_positions,
            cash_weight=1.0 - fsum(target_by_id.values()),
            one_way_turnover=one_way_turnover,
            gross_turnover=gross_turnover,
            total_estimated_cost=fsum(item.total_cost for item in orders),
            orders=tuple(orders),
            infeasibility_reasons=tuple(sorted(liquidity_failures)),
        )

    if one_way_turnover > specification.maximum_one_way_turnover + 1e-12:
        return PortfolioResult(
            specification_id=specification.specification_id,
            definition_version=specification.definition_version,
            horizon=specification.horizon,
            prediction_timestamp=prediction_timestamp,
            portfolio_notional=portfolio_notional,
            status=PortfolioRunStatus.INFEASIBLE_TURNOVER,
            target_positions=target_positions,
            cash_weight=1.0 - fsum(target_by_id.values()),
            one_way_turnover=one_way_turnover,
            gross_turnover=gross_turnover,
            total_estimated_cost=fsum(item.total_cost for item in orders),
            orders=tuple(orders),
            infeasibility_reasons=("MAXIMUM_ONE_WAY_TURNOVER_EXCEEDED",),
        )

    return PortfolioResult(
        specification_id=specification.specification_id,
        definition_version=specification.definition_version,
        horizon=specification.horizon,
        prediction_timestamp=prediction_timestamp,
        portfolio_notional=portfolio_notional,
        status=PortfolioRunStatus.CONSTRUCTED,
        target_positions=target_positions,
        cash_weight=1.0 - fsum(target_by_id.values()),
        one_way_turnover=one_way_turnover,
        gross_turnover=gross_turnover,
        total_estimated_cost=fsum(item.total_cost for item in orders),
        orders=tuple(orders),
        infeasibility_reasons=(),
    )
