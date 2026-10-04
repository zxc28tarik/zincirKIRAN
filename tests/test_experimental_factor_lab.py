from datetime import UTC, date, datetime

import pytest

from zincir_kiran.baselines import Horizon
from zincir_kiran.experimental_factor_lab import (
    AUTHORITY,
    DatedFactorCrossSection,
    ExperimentalFactorLabRunSpec,
    require_authoritative_promotion,
    run_experimental_factor_lab,
)
from zincir_kiran.experimental_factors import FactorDirection
from zincir_kiran.factor_lab import FactorObservation

PREREG = datetime(2026, 10, 4, 21, 0, tzinfo=UTC)
EXECUTED = datetime(2026, 10, 4, 21, 1, tzinfo=UTC)


def spec(direction: FactorDirection = FactorDirection.HIGHER_IS_BETTER):
    return ExperimentalFactorLabRunSpec(
        run_id="run-1",
        dataset_id="zk-experimental-factor-lab-v1",
        factor_id="example",
        factor_definition_version="v1",
        horizon=Horizon.H20,
        direction=direction,
        quantile_count=2,
        cost_model_id="research-zero-cost-diagnostic",
        preregistered_at=PREREG,
    )


def section(
    day: date,
    rows: list[tuple[str, float | None, float | None, str | None]],
) -> DatedFactorCrossSection:
    return DatedFactorCrossSection(
        as_of=day,
        observations=tuple(
            FactorObservation(
                security_id=security_id,
                factor_value=factor_value,
                forward_excess_return=forward_return,
                liquidity_tier=tier,
            )
            for security_id, factor_value, forward_return, tier in rows
        ),
    )


def test_higher_is_better_direction_preserves_positive_ic() -> None:
    sections = (
        section(
            date(2025, 1, 2),
            [
                ("A", 1.0, -0.03, "LIQUID_50"),
                ("B", 2.0, -0.01, "LIQUID_50"),
                ("C", 3.0, 0.01, "LIQUID_50"),
                ("D", 4.0, 0.03, "LIQUID_50"),
            ],
        ),
    )
    result = run_experimental_factor_lab(spec(), sections, executed_at=EXECUTED)
    assert result.ic_summary.mean_ic == pytest.approx(1.0)
    assert result.mean_top_vs_market == pytest.approx(0.02)
    assert result.mean_top_minus_bottom == pytest.approx(0.04)


def test_lower_is_better_direction_is_normalized_for_evaluation() -> None:
    sections = (
        section(
            date(2025, 1, 2),
            [
                ("A", 1.0, 0.03, "LIQUID_25"),
                ("B", 2.0, 0.01, "LIQUID_25"),
                ("C", 3.0, -0.01, "LIQUID_25"),
                ("D", 4.0, -0.03, "LIQUID_25"),
            ],
        ),
    )
    result = run_experimental_factor_lab(
        spec(FactorDirection.LOWER_IS_BETTER),
        sections,
        executed_at=EXECUTED,
    )
    assert result.ic_summary.mean_ic == pytest.approx(1.0)
    assert result.mean_top_vs_market == pytest.approx(0.02)


def test_insufficient_cross_section_remains_visible_as_unavailable_period() -> None:
    sections = (
        section(
            date(2025, 1, 2),
            [("A", 1.0, 0.01, "LIQUID_50")],
        ),
    )
    result = run_experimental_factor_lab(spec(), sections, executed_at=EXECUTED)
    assert result.periods[0].metrics is None
    assert result.periods[0].unavailable_reason == "INSUFFICIENT_USABLE_OBSERVATIONS"
    assert result.ic_summary.valid_periods == 0
    assert result.ic_summary.total_periods == 1
    assert result.mean_coverage == 0.0


def test_missing_factor_rows_reduce_coverage_without_neutral_fill() -> None:
    sections = (
        section(
            date(2025, 1, 2),
            [
                ("A", 1.0, 0.01, "LIQUID_50"),
                ("B", 2.0, 0.02, "LIQUID_50"),
                ("C", None, 0.03, "LIQUID_50"),
                ("D", 4.0, None, "LIQUID_50"),
            ],
        ),
    )
    result = run_experimental_factor_lab(spec(), sections, executed_at=EXECUTED)
    metrics = result.periods[0].metrics
    assert metrics is not None
    assert metrics.sample_size == 2
    assert metrics.total_observations == 4
    assert metrics.coverage == pytest.approx(0.5)


def test_liquidity_tiers_are_summarized_explicitly() -> None:
    sections = (
        section(
            date(2025, 1, 2),
            [
                ("A", 1.0, -0.03, "LIQUID_50"),
                ("B", 2.0, 0.03, "LIQUID_50"),
                ("C", 1.0, -0.02, "LIQUID_25"),
                ("D", 2.0, 0.02, "LIQUID_25"),
            ],
        ),
    )
    result = run_experimental_factor_lab(spec(), sections, executed_at=EXECUTED)
    tiers = {item.tier: item for item in result.liquidity_tiers}
    assert set(tiers) == {"LIQUID_25", "LIQUID_50"}
    assert tiers["LIQUID_25"].valid_periods == 1
    assert tiers["LIQUID_50"].mean_ic == pytest.approx(1.0)


def test_run_requires_chronological_unique_dates() -> None:
    later = section(date(2025, 2, 1), [("A", 1.0, 0.0, None), ("B", 2.0, 0.1, None)])
    earlier = section(date(2025, 1, 1), [("A", 1.0, 0.0, None), ("B", 2.0, 0.1, None)])
    with pytest.raises(ValueError, match="chronologically sorted"):
        run_experimental_factor_lab(spec(), (later, earlier), executed_at=EXECUTED)


def test_run_authority_and_promotion_are_fail_closed() -> None:
    sections = (
        section(
            date(2025, 1, 2),
            [("A", 1.0, 0.0, None), ("B", 2.0, 0.1, None)],
        ),
    )
    result = run_experimental_factor_lab(spec(), sections, executed_at=EXECUTED)
    assert result.authority == AUTHORITY
    with pytest.raises(ValueError, match="cannot authorize"):
        require_authoritative_promotion(result)


def test_execution_must_follow_preregistration() -> None:
    sections = (
        section(
            date(2025, 1, 2),
            [("A", 1.0, 0.0, None), ("B", 2.0, 0.1, None)],
        ),
    )
    with pytest.raises(ValueError, match="follow preregistration"):
        run_experimental_factor_lab(spec(), sections, executed_at=PREREG)
