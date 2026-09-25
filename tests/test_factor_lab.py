from datetime import UTC, date, datetime

import pytest

from zincir_kiran.baselines import Horizon
from zincir_kiran.factor_lab import (
    DatedIC,
    FactorExperimentRegistry,
    FactorExperimentSpec,
    FactorObservation,
    benjamini_hochberg_qvalues,
    cost_adjusted_return,
    equal_weight_turnover,
    evaluate_cross_section,
    liquidity_tier_metrics,
    prepare_sample,
    spearman_ic,
    summarize_ic_series,
)
from zincir_kiran.factor_library import ExpectedDirection


def observations() -> list[FactorObservation]:
    return [
        FactorObservation("A", 1.0, -0.04, "ALL"),
        FactorObservation("B", 2.0, -0.01, "ALL"),
        FactorObservation("C", 3.0, 0.02, "ALL"),
        FactorObservation("D", 4.0, 0.05, "ALL"),
    ]


def test_tie_aware_spearman_is_deterministic() -> None:
    left = (1.0, 1.0, 2.0, 3.0)
    right = (10.0, 20.0, 30.0, 40.0)
    first = spearman_ic(left, right)
    second = spearman_ic(left, right)
    assert first == second
    assert first is not None and 0 < first <= 1


def test_constant_factor_has_no_ic_not_zero_ic() -> None:
    assert spearman_ic((1.0, 1.0, 1.0), (0.1, 0.2, 0.3)) is None


def test_missing_rows_reduce_coverage_without_neutral_fill() -> None:
    rows = observations() + [
        FactorObservation("E", None, 0.10, "ALL"),
        FactorObservation("F", 6.0, None, "ALL"),
    ]
    sample = prepare_sample(rows)
    assert sample.used_observations == 4
    assert sample.total_observations == 6
    assert sample.coverage == pytest.approx(4 / 6)


def test_cross_section_reports_long_leg_separately() -> None:
    metrics = evaluate_cross_section(observations(), quantile_count=2)
    assert metrics.ic == pytest.approx(1.0)
    assert metrics.quantile_returns == pytest.approx((-0.025, 0.035))
    assert metrics.long_leg.top_vs_market == pytest.approx(0.035)
    assert metrics.long_leg.bottom_vs_market == pytest.approx(-0.025)
    assert metrics.long_leg.top_minus_bottom == pytest.approx(0.06)
    assert metrics.monotonicity == pytest.approx(1.0)


def test_ic_summary_does_not_turn_missing_period_into_zero() -> None:
    summary = summarize_ic_series([
        DatedIC(date(2026, 1, 1), 0.10),
        DatedIC(date(2026, 1, 2), None),
        DatedIC(date(2026, 1, 3), 0.20),
    ])
    assert summary.valid_periods == 2
    assert summary.total_periods == 3
    assert summary.mean_ic == pytest.approx(0.15)
    assert summary.icir is not None


def test_liquidity_tiers_are_not_mixed() -> None:
    rows = [
        FactorObservation("A", 1.0, -0.02, "LIQUID"),
        FactorObservation("B", 2.0, 0.03, "LIQUID"),
        FactorObservation("C", 1.0, -0.10, "ILLIQUID"),
        FactorObservation("D", 2.0, 0.20, "ILLIQUID"),
    ]
    result = liquidity_tier_metrics(rows, quantile_count=2)
    assert set(result) == {"ILLIQUID", "LIQUID"}
    assert result["LIQUID"].sample_size == 2
    assert result["ILLIQUID"].sample_size == 2


def test_equal_weight_turnover_and_explicit_cost() -> None:
    turnover = equal_weight_turnover(("A", "B"), ("B", "C"))
    assert turnover == pytest.approx(0.5)
    assert cost_adjusted_return(
        0.04,
        turnover=turnover,
        cost_per_unit_turnover=0.01,
    ) == pytest.approx(0.035)


def test_cost_adjustment_has_no_hidden_default() -> None:
    with pytest.raises(TypeError):
        cost_adjusted_return(0.04, turnover=0.5)  # type: ignore[call-arg]


def test_benjamini_hochberg_qvalues_are_monotone_adjusted() -> None:
    qvalues = benjamini_hochberg_qvalues({"a": 0.01, "b": 0.04, "c": 0.20})
    assert qvalues["a"] == pytest.approx(0.03)
    assert qvalues["b"] == pytest.approx(0.06)
    assert qvalues["c"] == pytest.approx(0.20)


def test_experiment_preregistration_is_immutable() -> None:
    registry = FactorExperimentRegistry()
    spec = FactorExperimentSpec(
        experiment_id="exp-1",
        factor_id="book_to_price",
        factor_definition_version="v1",
        horizon=Horizon.H20,
        data_snapshot_id="snapshot-1",
        universe_rule_version="universe-v1",
        quantile_count=5,
        cost_model_id="cost-v1",
        hypothesis="Higher book-to-price predicts higher future excess return.",
        expected_direction=ExpectedDirection.HIGHER_IS_BETTER,
        preregistered_at=datetime(2026, 9, 25, tzinfo=UTC),
    )
    registry.register(spec)
    registry.register(spec)

    with pytest.raises(ValueError, match="conflicting"):
        registry.register(
            FactorExperimentSpec(
                experiment_id="exp-1",
                factor_id="book_to_price",
                factor_definition_version="v1",
                horizon=Horizon.H20,
                data_snapshot_id="snapshot-1",
                universe_rule_version="universe-v1",
                quantile_count=10,
                cost_model_id="cost-v1",
                hypothesis="Changed after seeing results.",
                expected_direction=ExpectedDirection.HIGHER_IS_BETTER,
                preregistered_at=datetime(2026, 9, 25, tzinfo=UTC),
            )
        )
