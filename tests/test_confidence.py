from datetime import UTC, datetime, timedelta

import pytest

from zincir_kiran.alpha_aggregation import AlphaAggregationSpec
from zincir_kiran.alpha_engine import AlphaExecutionStatus, InterpretableAlphaResult
from zincir_kiran.baselines import Horizon
from zincir_kiran.confidence import (
    ConfidenceAvailability,
    ConfidenceDecision,
    ConfidenceDimensionKind,
    ConfidenceDimensionSpec,
    ConfidenceObservation,
    ConfidenceRegistry,
    ConfidenceSpec,
    evaluate_confidence,
)

PREDICTION = datetime(2026, 10, 4, 9, tzinfo=UTC)


def base_spec() -> AlphaAggregationSpec:
    return AlphaAggregationSpec(
        specification_id="alpha-h20-base",
        definition_version="v1",
        horizon=Horizon.H20,
        aggregation_rule_id="WEIGHTED_ABS_MEAN",
        normalization_rule_id="ALPHA_NORM",
        weight_policy_id="STATIC",
        coverage_rule_id="ABS_WEIGHT_COVERAGE",
        parameters=(("minimum_coverage", "0.75"),),
    )


def alpha_result(
    *,
    status: AlphaExecutionStatus = AlphaExecutionStatus.SCORED,
    alpha_value: float | None = -0.35,
) -> InterpretableAlphaResult:
    return InterpretableAlphaResult(
        security_id="SEC-1",
        horizon=Horizon.H20,
        alpha_field="Alpha20",
        specification_id="alpha-h20-base",
        definition_version="v1",
        status=status,
        alpha_value=alpha_value,
        coverage=1.0 if status is AlphaExecutionStatus.SCORED else 0.5,
        planned_factor_count=2,
        available_factor_count=2 if status is AlphaExecutionStatus.SCORED else 1,
        planned_absolute_weight=2.0,
        available_absolute_weight=(
            2.0 if status is AlphaExecutionStatus.SCORED else 1.0
        ),
        contributions=(),
        unavailable_inputs=(),
    )


def dimensions() -> tuple[ConfidenceDimensionSpec, ...]:
    return (
        ConfidenceDimensionSpec(
            "data_coverage",
            ConfidenceDimensionKind.DATA_COVERAGE,
            True,
            5,
            2.0,
            0.50,
            1.00,
            0.60,
        ),
        ConfidenceDimensionSpec(
            "factor_evidence",
            ConfidenceDimensionKind.FACTOR_EVIDENCE,
            True,
            30,
            2.0,
            0.00,
            1.00,
            0.40,
        ),
        ConfidenceDimensionSpec(
            "freshness",
            ConfidenceDimensionKind.FRESHNESS,
            True,
            5,
            1.0,
            0.00,
            1.00,
            0.50,
        ),
        ConfidenceDimensionSpec(
            "liquidity",
            ConfidenceDimensionKind.LIQUIDITY,
            False,
            5,
            1.0,
            0.00,
            1.00,
            0.30,
        ),
        ConfidenceDimensionSpec(
            "model_agreement",
            ConfidenceDimensionKind.MODEL_AGREEMENT,
            False,
            5,
            1.0,
            0.00,
            1.00,
            None,
        ),
        ConfidenceDimensionSpec(
            "pit_certainty",
            ConfidenceDimensionKind.PIT_CERTAINTY,
            True,
            30,
            1.0,
            0.00,
            1.00,
            0.70,
        ),
    )


def confidence_spec(**overrides: object) -> ConfidenceSpec:
    values: dict[str, object] = {
        "specification_id": "confidence-h20",
        "definition_version": "v1",
        "horizon": Horizon.H20,
        "base_alpha_specification_id": "alpha-h20-base",
        "base_alpha_definition_version": "v1",
        "confidence_protocol_id": "confidence-protocol-v1",
        "universe_rule_version": "universe-v1",
        "hypothesis": "Evidence quality should gate whether Alpha is actionable.",
        "success_criteria": "Reduce fragile signals without changing Alpha.",
        "preregistered_at": PREDICTION - timedelta(days=30),
        "minimum_weight_coverage": 0.75,
        "signal_eligibility_threshold": 0.65,
        "dimensions": dimensions(),
    }
    values.update(overrides)
    return ConfidenceSpec(**values)  # type: ignore[arg-type]


def observation(
    dimension_id: str,
    raw_value: float,
    *,
    age_days: int = 1,
    protocol: str = "confidence-protocol-v1",
    security_id: str = "SEC-1",
) -> ConfidenceObservation:
    end = PREDICTION - timedelta(days=age_days)
    return ConfidenceObservation(
        observation_id=f"obs-{dimension_id}",
        security_id=security_id,
        dimension_id=dimension_id,
        confidence_protocol_id=protocol,
        raw_value=raw_value,
        window_start=end - timedelta(days=10),
        window_end=end,
        available_at=end + timedelta(hours=1),
        source_reference=f"source-{dimension_id}",
    )


def strong_observations() -> list[ConfidenceObservation]:
    return [
        observation("data_coverage", 0.95),
        observation("factor_evidence", 0.80),
        observation("freshness", 0.90),
        observation("liquidity", 0.80),
        observation("model_agreement", 0.75),
        observation("pit_certainty", 0.95),
    ]


def test_confidence_registry_rejects_conflicting_rewrite() -> None:
    registry = ConfidenceRegistry()
    item = confidence_spec()
    registry.register(item)
    registry.register(item)
    with pytest.raises(ValueError, match="conflicting"):
        registry.register(confidence_spec(signal_eligibility_threshold=0.90))


def test_future_confidence_evidence_is_rejected() -> None:
    future_end = PREDICTION + timedelta(days=1)
    future = ConfidenceObservation(
        observation_id="future",
        security_id="SEC-1",
        dimension_id="data_coverage",
        confidence_protocol_id="confidence-protocol-v1",
        raw_value=0.9,
        window_start=PREDICTION - timedelta(days=5),
        window_end=future_end,
        available_at=future_end + timedelta(hours=1),
        source_reference="future-source",
    )
    observations = [
        future,
        *[
            item
            for item in strong_observations()
            if item.dimension_id != "data_coverage"
        ],
    ]
    with pytest.raises(ValueError, match="future confidence"):
        evaluate_confidence(
            specification=confidence_spec(),
            base_alpha_specification=base_spec(),
            alpha_result=alpha_result(),
            observations=observations,
            prediction_timestamp=PREDICTION,
        )


def test_required_missing_evidence_produces_no_signal_without_neutral_fill() -> None:
    observations = [
        item
        for item in strong_observations()
        if item.dimension_id != "pit_certainty"
    ]
    result = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=observations,
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.NO_SIGNAL_REQUIRED_EVIDENCE
    assert result.confidence_score is None
    by_dimension = {item.dimension_id: item for item in result.dimension_results}
    assert by_dimension["pit_certainty"].availability is ConfidenceAvailability.MISSING
    assert by_dimension["pit_certainty"].normalized_quality is None


def test_required_stale_evidence_produces_no_signal() -> None:
    observations = [
        observation("data_coverage", 0.95),
        observation("factor_evidence", 0.80),
        observation("freshness", 0.90, age_days=6),
        observation("pit_certainty", 0.95),
    ]
    result = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=observations,
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.NO_SIGNAL_REQUIRED_EVIDENCE
    by_dimension = {item.dimension_id: item for item in result.dimension_results}
    assert by_dimension["freshness"].availability is ConfidenceAvailability.STALE


def test_optional_missing_evidence_reduces_coverage_but_is_not_neutral() -> None:
    observations = [
        item
        for item in strong_observations()
        if item.dimension_id not in {"liquidity", "model_agreement"}
    ]
    result = evaluate_confidence(
        specification=confidence_spec(minimum_weight_coverage=0.70),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=observations,
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.SIGNAL_ELIGIBLE
    assert result.evidence_weight_coverage == pytest.approx(0.75)
    by_dimension = {item.dimension_id: item for item in result.dimension_results}
    assert by_dimension["liquidity"].normalized_quality is None
    assert by_dimension["model_agreement"].normalized_quality is None


def test_insufficient_optional_coverage_can_still_force_no_signal() -> None:
    custom = tuple(
        ConfidenceDimensionSpec(
            item.dimension_id,
            item.kind,
            item.required,
            item.max_age_days,
            item.weight,
            item.bad_reference,
            item.good_reference,
            item.hard_floor,
        )
        for item in dimensions()
    )
    observations = [
        item
        for item in strong_observations()
        if item.dimension_id not in {"liquidity", "model_agreement"}
    ]
    result = evaluate_confidence(
        specification=confidence_spec(
            dimensions=custom,
            minimum_weight_coverage=0.90,
        ),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=observations,
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.NO_SIGNAL_INSUFFICIENT_COVERAGE
    assert result.confidence_score is None


def test_hard_floor_failure_produces_no_signal_with_auditable_score() -> None:
    observations = [
        observation("data_coverage", 0.95),
        observation("factor_evidence", 0.80),
        observation("freshness", 0.90),
        observation("liquidity", 0.10),
        observation("model_agreement", 0.90),
        observation("pit_certainty", 0.95),
    ]
    result = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=observations,
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.NO_SIGNAL_HARD_FLOOR
    assert result.confidence_score is not None
    assert "HARD_FLOOR:liquidity" in result.abstention_reasons


def test_low_weighted_confidence_produces_no_signal() -> None:
    observations = [
        observation("data_coverage", 0.80),
        observation("factor_evidence", 0.50),
        observation("freshness", 0.55),
        observation("liquidity", 0.50),
        observation("model_agreement", 0.40),
        observation("pit_certainty", 0.75),
    ]
    result = evaluate_confidence(
        specification=confidence_spec(signal_eligibility_threshold=0.70),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=observations,
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.NO_SIGNAL_LOW_CONFIDENCE
    assert result.confidence_score is not None
    assert result.confidence_score < 0.70


def test_strong_confidence_can_make_negative_alpha_signal_eligible_without_changing_it() -> None:
    source = alpha_result(alpha_value=-0.35)
    result = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=source,
        observations=strong_observations(),
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.SIGNAL_ELIGIBLE
    assert result.source_alpha_value == -0.35
    assert source.alpha_value == -0.35
    assert result.confidence_score is not None
    assert result.confidence_score >= 0.65


def test_alpha_abstention_cannot_be_overridden_by_high_confidence_evidence() -> None:
    source = alpha_result(
        status=AlphaExecutionStatus.ABSTAIN_INSUFFICIENT_COVERAGE,
        alpha_value=None,
    )
    result = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=source,
        observations=strong_observations(),
        prediction_timestamp=PREDICTION,
    )
    assert result.decision is ConfidenceDecision.NO_SIGNAL_ALPHA_UNAVAILABLE
    assert result.confidence_score is None
    assert result.source_alpha_value is None


def test_protocol_and_security_mismatch_are_rejected() -> None:
    bad_protocol = [
        observation("data_coverage", 0.95, protocol="post-hoc"),
        *[
            item
            for item in strong_observations()
            if item.dimension_id != "data_coverage"
        ],
    ]
    with pytest.raises(ValueError, match="protocol mismatch"):
        evaluate_confidence(
            specification=confidence_spec(),
            base_alpha_specification=base_spec(),
            alpha_result=alpha_result(),
            observations=bad_protocol,
            prediction_timestamp=PREDICTION,
        )

    bad_security = [
        observation("data_coverage", 0.95, security_id="OTHER"),
        *[
            item
            for item in strong_observations()
            if item.dimension_id != "data_coverage"
        ],
    ]
    with pytest.raises(ValueError, match="security mismatch"):
        evaluate_confidence(
            specification=confidence_spec(),
            base_alpha_specification=base_spec(),
            alpha_result=alpha_result(),
            observations=bad_security,
            prediction_timestamp=PREDICTION,
        )


def test_post_hoc_confidence_spec_is_rejected() -> None:
    with pytest.raises(ValueError, match="preregistered"):
        evaluate_confidence(
            specification=confidence_spec(
                preregistered_at=PREDICTION + timedelta(seconds=1)
            ),
            base_alpha_specification=base_spec(),
            alpha_result=alpha_result(),
            observations=strong_observations(),
            prediction_timestamp=PREDICTION,
        )


def test_fixed_inputs_are_deterministic_independent_of_observation_order() -> None:
    first = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=strong_observations(),
        prediction_timestamp=PREDICTION,
    )
    second = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=list(reversed(strong_observations())),
        prediction_timestamp=PREDICTION,
    )
    assert first == second


def test_confidence_output_contains_no_portfolio_or_alpha_mutation_fields() -> None:
    result = evaluate_confidence(
        specification=confidence_spec(),
        base_alpha_specification=base_spec(),
        alpha_result=alpha_result(),
        observations=strong_observations(),
        prediction_timestamp=PREDICTION,
    )
    assert not hasattr(result, "portfolio_weight")
    assert not hasattr(result, "position_size")
    assert not hasattr(result, "adjusted_alpha")

def test_zero_minimum_coverage_is_rejected() -> None:
    with pytest.raises(ValueError, match="minimum_weight_coverage"):
        confidence_spec(minimum_weight_coverage=0.0)


def test_malformed_source_alpha_state_is_rejected() -> None:
    malformed = alpha_result(alpha_value=None)
    with pytest.raises(ValueError, match="SCORED alpha result"):
        evaluate_confidence(
            specification=confidence_spec(),
            base_alpha_specification=base_spec(),
            alpha_result=malformed,
            observations=strong_observations(),
            prediction_timestamp=PREDICTION,
        )
