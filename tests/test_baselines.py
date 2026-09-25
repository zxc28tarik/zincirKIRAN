from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction

import pytest

from zincir_kiran.baselines import (
    REQUIRED_BASELINES,
    BaselineDefinition,
    BaselineId,
    BaselineRegistry,
    BaselineRole,
    BaselineRunSpec,
    Horizon,
    baseline_role,
    equal_weight,
    market_relative_return,
)


def test_required_baseline_identities_are_locked() -> None:
    assert set(REQUIRED_BASELINES) == {
        BaselineId.MARKET_BENCHMARK,
        BaselineId.EQUAL_WEIGHT,
        BaselineId.SIMPLE_VALUE,
        BaselineId.SIMPLE_MOMENTUM,
        BaselineId.QVM,
        BaselineId.TURKISH_FACTOR,
        BaselineId.TOTAL_RASYO,
    }
    assert baseline_role(BaselineId.TOTAL_RASYO) is BaselineRole.FAILED_REFERENCE


def test_horizons_are_separate_trading_day_contracts() -> None:
    assert {horizon.value for horizon in Horizon} == {20, 60, 120, 252}


def test_equal_weight_is_deterministic_and_exact() -> None:
    assert equal_weight(["B", "A", "C"]) == (
        ("A", Fraction(1, 3)),
        ("B", Fraction(1, 3)),
        ("C", Fraction(1, 3)),
    )


def test_equal_weight_rejects_duplicate_security() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        equal_weight(["A", "A"])


def test_market_relative_return_is_explicit() -> None:
    assert market_relative_return(Decimal("0.12"), Decimal("0.05")) == Decimal("0.07")
    with pytest.raises(ValueError, match="missing return"):
        market_relative_return(None, Decimal("0.05"))


def test_conflicting_baseline_definition_rewrite_is_rejected() -> None:
    registry = BaselineRegistry()
    original = BaselineDefinition(
        baseline_id=BaselineId.SIMPLE_VALUE,
        definition_version="v1",
        formula="PRE_REGISTERED_FORMULA_A",
    )
    registry.register(original)
    registry.register(original)

    with pytest.raises(ValueError, match="conflicting"):
        registry.register(
            BaselineDefinition(
                baseline_id=BaselineId.SIMPLE_VALUE,
                definition_version="v1",
                formula="CHANGED_AFTER_RESULTS",
            )
        )


def test_run_spec_requires_explicit_research_metadata() -> None:
    with pytest.raises(ValueError, match="data_snapshot_id"):
        BaselineRunSpec(
            baseline_id=BaselineId.EQUAL_WEIGHT,
            definition_version="v1",
            horizon=Horizon.H20,
            data_snapshot_id="",
            universe_rule_version="u1",
            rebalance_specification="explicit-test-rule",
            created_at=datetime(2026, 9, 25, tzinfo=UTC),
        )
