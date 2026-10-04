from datetime import UTC, datetime, timedelta

import pytest

from zincir_kiran.alpha_engine import AlphaExecutionStatus, InterpretableAlphaResult
from zincir_kiran.baselines import Horizon
from zincir_kiran.confidence import ConfidenceDecision, ConfidenceResult
from zincir_kiran.portfolio import (
    CurrentHolding,
    ExecutionEvidence,
    PortfolioCandidate,
    PortfolioRunStatus,
    PortfolioSpec,
    PortfolioSpecRegistry,
    SelectionRule,
    SizingRule,
    construct_portfolio,
)

PREDICTION = datetime(2026, 10, 4, 9, tzinfo=UTC)


def alpha(security_id: str, value: float) -> InterpretableAlphaResult:
    return InterpretableAlphaResult(
        security_id=security_id,
        horizon=Horizon.H20,
        alpha_field="Alpha20",
        specification_id="alpha-h20",
        definition_version="v1",
        status=AlphaExecutionStatus.SCORED,
        alpha_value=value,
        coverage=1.0,
        planned_factor_count=2,
        available_factor_count=2,
        planned_absolute_weight=2.0,
        available_absolute_weight=2.0,
        contributions=(),
        unavailable_inputs=(),
    )


def confidence(
    security_id: str,
    alpha_value: float,
    *,
    decision: ConfidenceDecision = ConfidenceDecision.SIGNAL_ELIGIBLE,
    score: float | None = 0.8,
) -> ConfidenceResult:
    return ConfidenceResult(
        specification_id="confidence-h20",
        definition_version="v1",
        security_id=security_id,
        horizon=Horizon.H20,
        prediction_timestamp=PREDICTION,
        source_alpha_specification_id="alpha-h20",
        source_alpha_definition_version="v1",
        source_alpha_value=alpha_value,
        decision=decision,
        confidence_score=score,
        evidence_weight_coverage=1.0,
        available_weight=1.0,
        total_weight=1.0,
        dimension_results=(),
        abstention_reasons=(),
    )


def candidate(
    security_id: str,
    sector_id: str,
    alpha_value: float,
    *,
    decision: ConfidenceDecision = ConfidenceDecision.SIGNAL_ELIGIBLE,
) -> PortfolioCandidate:
    return PortfolioCandidate(
        security_id=security_id,
        sector_id=sector_id,
        alpha_result=alpha(security_id, alpha_value),
        confidence_result=confidence(
            security_id,
            alpha_value,
            decision=decision,
            score=0.8 if decision is ConfidenceDecision.SIGNAL_ELIGIBLE else None,
        ),
    )


def spec(**overrides: object) -> PortfolioSpec:
    values: dict[str, object] = {
        "specification_id": "portfolio-h20",
        "definition_version": "v1",
        "horizon": Horizon.H20,
        "base_alpha_specification_id": "alpha-h20",
        "base_alpha_definition_version": "v1",
        "confidence_specification_id": "confidence-h20",
        "confidence_definition_version": "v1",
        "universe_rule_version": "universe-v1",
        "hypothesis": "Eligible Alpha can be converted into feasible long-only holdings.",
        "success_criteria": "Respect all constraints and costs without hidden relaxation.",
        "preregistered_at": PREDICTION - timedelta(days=30),
        "selection_rule": SelectionRule.TOP_ALPHA,
        "sizing_rule": SizingRule.EQUAL_WEIGHT,
        "rebalance_rule_id": "REBALANCE_TO_BE_SELECTED_BY_EVIDENCE",
        "target_position_count": 3,
        "minimum_position_count": 2,
        "minimum_alpha_value": 0.0,
        "target_invested_weight": 0.90,
        "max_single_name_weight": 0.40,
        "max_sector_weight": 0.60,
        "max_participation_rate": 0.10,
        "execution_days": 2,
        "max_liquidity_age_days": 5,
        "maximum_one_way_turnover": 1.0,
    }
    values.update(overrides)
    return PortfolioSpec(**values)  # type: ignore[arg-type]


def evidence(
    security_id: str,
    *,
    adv: float = 10_000_000.0,
    age_days: int = 1,
    commission_bps: float = 5.0,
    spread_bps: float = 10.0,
    slippage_bps: float = 5.0,
    impact_bps: float = 10.0,
) -> ExecutionEvidence:
    end = PREDICTION - timedelta(days=age_days)
    return ExecutionEvidence(
        security_id=security_id,
        window_end=end,
        available_at=end + timedelta(hours=1),
        average_daily_notional=adv,
        commission_bps=commission_bps,
        half_spread_bps=spread_bps,
        slippage_bps=slippage_bps,
        market_impact_bps=impact_bps,
        source_reference=f"liq-{security_id}",
    )


def eligible_universe() -> list[PortfolioCandidate]:
    return [
        candidate("A", "BANK", 0.9),
        candidate("B", "BANK", 0.8),
        candidate("C", "INDUSTRY", 0.7),
        candidate("D", "RETAIL", 0.6),
    ]


def all_evidence(*security_ids: str) -> list[ExecutionEvidence]:
    return [evidence(security_id) for security_id in security_ids]


def test_portfolio_spec_registry_rejects_conflicting_rewrite() -> None:
    registry = PortfolioSpecRegistry()
    item = spec()
    registry.register(item)
    registry.register(item)
    with pytest.raises(ValueError, match="conflicting"):
        registry.register(spec(target_position_count=5))


def test_only_signal_eligible_candidates_can_be_selected() -> None:
    universe = [
        candidate("A", "BANK", 0.9),
        candidate(
            "B",
            "INDUSTRY",
            0.95,
            decision=ConfidenceDecision.NO_SIGNAL_LOW_CONFIDENCE,
        ),
        candidate("C", "RETAIL", 0.8),
    ]
    result = construct_portfolio(
        specification=spec(target_position_count=2, minimum_position_count=2),
        candidates=universe,
        current_holdings=[],
        execution_evidence=all_evidence("A", "C"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.CONSTRUCTED
    assert tuple(item.security_id for item in result.target_positions) == ("A", "C")


def test_selection_is_deterministic_by_alpha_then_security_id() -> None:
    universe = [
        candidate("B", "BANK", 0.8),
        candidate("A", "INDUSTRY", 0.8),
        candidate("C", "RETAIL", 0.7),
    ]
    first = construct_portfolio(
        specification=spec(target_position_count=2, minimum_position_count=2),
        candidates=universe,
        current_holdings=[],
        execution_evidence=all_evidence("A", "B"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    second = construct_portfolio(
        specification=spec(target_position_count=2, minimum_position_count=2),
        candidates=list(reversed(universe)),
        current_holdings=[],
        execution_evidence=all_evidence("B", "A"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert first == second
    assert tuple(item.security_id for item in first.target_positions) == ("A", "B")


def test_insufficient_eligible_names_is_explicitly_infeasible() -> None:
    result = construct_portfolio(
        specification=spec(minimum_position_count=3),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate(
                "B",
                "INDUSTRY",
                0.8,
                decision=ConfidenceDecision.NO_SIGNAL_LOW_CONFIDENCE,
            ),
        ],
        current_holdings=[],
        execution_evidence=[],
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.INFEASIBLE_INSUFFICIENT_ELIGIBLE
    assert result.infeasibility_reasons == ("INSUFFICIENT_ELIGIBLE_SECURITIES",)


def test_single_name_and_sector_caps_are_enforced_without_relaxation() -> None:
    result = construct_portfolio(
        specification=spec(
            target_position_count=2,
            minimum_position_count=2,
            target_invested_weight=0.90,
            max_single_name_weight=0.60,
            max_sector_weight=0.40,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "BANK", 0.8),
        ],
        current_holdings=[],
        execution_evidence=[],
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.INFEASIBLE_CONSTRAINTS
    assert result.infeasibility_reasons == ("WEIGHT_OR_SECTOR_CAPS_INFEASIBLE",)


def test_equal_weight_allocation_respects_caps_and_cash_residual() -> None:
    result = construct_portfolio(
        specification=spec(),
        candidates=eligible_universe(),
        current_holdings=[],
        execution_evidence=all_evidence("A", "B", "C"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.CONSTRUCTED
    assert tuple(item.security_id for item in result.target_positions) == ("A", "B", "C")
    assert sum(item.target_weight for item in result.target_positions) == pytest.approx(0.90)
    assert result.cash_weight == pytest.approx(0.10)
    bank_weight = sum(
        item.target_weight
        for item in result.target_positions
        if item.sector_id == "BANK"
    )
    assert bank_weight <= 0.60 + 1e-12
    assert all(item.target_weight <= 0.40 + 1e-12 for item in result.target_positions)


def test_positive_alpha_proportional_sizing_is_explicit() -> None:
    result = construct_portfolio(
        specification=spec(
            sizing_rule=SizingRule.POSITIVE_ALPHA_PROPORTIONAL,
            target_position_count=2,
            minimum_position_count=2,
            target_invested_weight=0.60,
            max_single_name_weight=0.60,
            max_sector_weight=1.0,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.3),
        ],
        current_holdings=[],
        execution_evidence=all_evidence("A", "B"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    by_id = {item.security_id: item.target_weight for item in result.target_positions}
    assert result.status is PortfolioRunStatus.CONSTRUCTED
    assert by_id["A"] == pytest.approx(0.45)
    assert by_id["B"] == pytest.approx(0.15)


def test_missing_execution_evidence_never_means_unlimited_liquidity() -> None:
    result = construct_portfolio(
        specification=spec(target_position_count=2, minimum_position_count=2),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.8),
        ],
        current_holdings=[],
        execution_evidence=[evidence("A")],
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.INFEASIBLE_LIQUIDITY
    assert "MISSING_EXECUTION_EVIDENCE:B" in result.infeasibility_reasons


def test_stale_and_future_execution_evidence_are_not_usable() -> None:
    stale_result = construct_portfolio(
        specification=spec(
            target_position_count=2,
            minimum_position_count=2,
            max_liquidity_age_days=2,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.8),
        ],
        current_holdings=[],
        execution_evidence=[evidence("A"), evidence("B", age_days=3)],
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert stale_result.status is PortfolioRunStatus.INFEASIBLE_LIQUIDITY
    assert "STALE_EXECUTION_EVIDENCE:B" in stale_result.infeasibility_reasons

    future_end = PREDICTION + timedelta(days=1)
    future = ExecutionEvidence(
        security_id="B",
        window_end=future_end,
        available_at=future_end + timedelta(hours=1),
        average_daily_notional=10_000_000,
        commission_bps=5,
        half_spread_bps=10,
        slippage_bps=5,
        market_impact_bps=10,
        source_reference="future",
    )
    with pytest.raises(ValueError, match="future execution evidence"):
        construct_portfolio(
            specification=spec(target_position_count=2, minimum_position_count=2),
            candidates=[
                candidate("A", "BANK", 0.9),
                candidate("B", "INDUSTRY", 0.8),
            ],
            current_holdings=[],
            execution_evidence=[evidence("A"), future],
            prediction_timestamp=PREDICTION,
            portfolio_notional=1_000_000,
        )


def test_capacity_limit_is_enforced_per_trade() -> None:
    result = construct_portfolio(
        specification=spec(
            target_position_count=2,
            minimum_position_count=2,
            max_participation_rate=0.01,
            execution_days=1,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.8),
        ],
        current_holdings=[],
        execution_evidence=[
            evidence("A", adv=1_000_000),
            evidence("B", adv=1_000_000),
        ],
        prediction_timestamp=PREDICTION,
        portfolio_notional=10_000_000,
    )
    assert result.status is PortfolioRunStatus.INFEASIBLE_LIQUIDITY
    assert any(reason.startswith("CAPACITY_EXCEEDED:") for reason in result.infeasibility_reasons)


def test_turnover_includes_entries_exits_and_weight_changes() -> None:
    result = construct_portfolio(
        specification=spec(
            target_position_count=2,
            minimum_position_count=2,
            target_invested_weight=0.80,
            max_single_name_weight=0.50,
            max_sector_weight=1.0,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.8),
        ],
        current_holdings=[
            CurrentHolding("A", 0.20),
            CurrentHolding("C", 0.30),
        ],
        execution_evidence=all_evidence("A", "B", "C"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.CONSTRUCTED
    # target A=0.4, B=0.4: |+.2| + |+.4| + |-.3| = .9 gross; .45 one-way
    assert result.gross_turnover == pytest.approx(0.90)
    assert result.one_way_turnover == pytest.approx(0.45)
    by_id = {order.security_id: order for order in result.orders}
    assert by_id["C"].target_weight == 0.0
    assert by_id["C"].delta_weight == pytest.approx(-0.30)


def test_transaction_cost_components_are_separate_and_sum_exactly() -> None:
    result = construct_portfolio(
        specification=spec(
            target_position_count=2,
            minimum_position_count=2,
            target_invested_weight=0.80,
            max_single_name_weight=0.50,
            max_sector_weight=1.0,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.8),
        ],
        current_holdings=[],
        execution_evidence=all_evidence("A", "B"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    order = next(item for item in result.orders if item.security_id == "A")
    assert order.trade_notional == pytest.approx(400_000)
    assert order.commission_cost == pytest.approx(200)
    assert order.spread_cost == pytest.approx(400)
    assert order.slippage_cost == pytest.approx(200)
    assert order.market_impact_cost == pytest.approx(400)
    assert order.total_cost == pytest.approx(1200)
    assert result.total_estimated_cost == pytest.approx(2400)


def test_maximum_turnover_can_make_an_otherwise_valid_plan_infeasible() -> None:
    result = construct_portfolio(
        specification=spec(
            target_position_count=2,
            minimum_position_count=2,
            target_invested_weight=0.80,
            max_single_name_weight=0.50,
            max_sector_weight=1.0,
            maximum_one_way_turnover=0.20,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.8),
        ],
        current_holdings=[],
        execution_evidence=all_evidence("A", "B"),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.INFEASIBLE_TURNOVER
    assert result.one_way_turnover == pytest.approx(0.40)


def test_alpha_and_confidence_source_values_are_preserved() -> None:
    item = candidate("A", "BANK", 0.9)
    result = construct_portfolio(
        specification=spec(target_position_count=1, minimum_position_count=1),
        candidates=[item],
        current_holdings=[],
        execution_evidence=[evidence("A")],
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    target = result.target_positions[0]
    assert target.alpha_value == 0.9
    assert target.confidence_score == 0.8
    assert item.alpha_result.alpha_value == 0.9
    assert item.confidence_result.source_alpha_value == 0.9


def test_fixed_inputs_are_deterministic_independent_of_input_order() -> None:
    universe = eligible_universe()
    holdings = [CurrentHolding("A", 0.1), CurrentHolding("D", 0.2)]
    evidences = all_evidence("A", "B", "C", "D")
    first = construct_portfolio(
        specification=spec(),
        candidates=universe,
        current_holdings=holdings,
        execution_evidence=evidences,
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    second = construct_portfolio(
        specification=spec(),
        candidates=list(reversed(universe)),
        current_holdings=list(reversed(holdings)),
        execution_evidence=list(reversed(evidences)),
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert first == second

def test_signal_eligible_candidate_requires_finite_confidence_score() -> None:
    malformed = PortfolioCandidate(
        security_id="A",
        sector_id="BANK",
        alpha_result=alpha("A", 0.9),
        confidence_result=confidence(
            "A",
            0.9,
            decision=ConfidenceDecision.SIGNAL_ELIGIBLE,
            score=None,
        ),
    )
    with pytest.raises(ValueError, match="finite Confidence"):
        construct_portfolio(
            specification=spec(target_position_count=1, minimum_position_count=1),
            candidates=[malformed],
            current_holdings=[],
            execution_evidence=[evidence("A")],
            prediction_timestamp=PREDICTION,
            portfolio_notional=1_000_000,
        )

def test_positive_alpha_proportional_nonpositive_selection_is_infeasible() -> None:
    result = construct_portfolio(
        specification=spec(
            sizing_rule=SizingRule.POSITIVE_ALPHA_PROPORTIONAL,
            target_position_count=2,
            minimum_position_count=2,
            minimum_alpha_value=-1.0,
            max_sector_weight=1.0,
        ),
        candidates=[
            candidate("A", "BANK", 0.9),
            candidate("B", "INDUSTRY", 0.0),
        ],
        current_holdings=[],
        execution_evidence=[],
        prediction_timestamp=PREDICTION,
        portfolio_notional=1_000_000,
    )
    assert result.status is PortfolioRunStatus.INFEASIBLE_CONSTRAINTS
