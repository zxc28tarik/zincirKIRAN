from datetime import UTC, datetime, timedelta

import pytest

from zincir_kiran.alpha_aggregation import AlphaAggregationSpec
from zincir_kiran.alpha_engine import AlphaFactorWeight
from zincir_kiran.baselines import Horizon
from zincir_kiran.context_research import (
    ContextFactorSignal,
    ContextResearchRegistry,
    ContextResearchSpec,
    ContextRunStatus,
    ContradictionRule,
    InteractionRule,
    InteractionState,
    RegimeAvailability,
    RegimeDimensionSpec,
    RegimeObservation,
    RegimeStateRule,
    evaluate_context_research,
)
from zincir_kiran.interpretable_alpha import AdmissionDecision, FactorAdmission

PREDICTION = datetime(2026, 10, 4, 9, tzinfo=UTC)


def admission(factor_id: str, component: int) -> FactorAdmission:
    return FactorAdmission(
        admission_id=f"adm-{factor_id}",
        factor_id=factor_id,
        factor_definition_version="v1",
        horizon=Horizon.H20,
        decision=AdmissionDecision.ADMITTED,
        factor_lab_experiment_id=f"exp-{factor_id}",
        decorrelation_run_id="decor-h20",
        decorrelation_component_no=component,
        rationale="test admission",
    )


VALUE = admission("value", 1)
MOMENTUM = admission("momentum", 2)


def base_spec() -> AlphaAggregationSpec:
    return AlphaAggregationSpec(
        specification_id="alpha-h20-base",
        definition_version="v1",
        horizon=Horizon.H20,
        aggregation_rule_id="WEIGHTED_ABS_MEAN",
        normalization_rule_id="ALPHA_NORM",
        weight_policy_id="STATIC_TEST_WEIGHTS",
        coverage_rule_id="ABS_WEIGHT_COVERAGE",
        parameters=(("minimum_coverage", "0.75"),),
    )


def regime_dimensions() -> tuple[RegimeDimensionSpec, ...]:
    return (
        RegimeDimensionSpec(
            dimension_id="macro_axis",
            max_age_days=40,
            state_rules=(
                RegimeStateRule("state_low", None, 0.0),
                RegimeStateRule("state_high", 0.0, None),
            ),
        ),
        RegimeDimensionSpec(
            dimension_id="risk_axis",
            max_age_days=10,
            state_rules=(
                RegimeStateRule("state_quiet", None, 1.0),
                RegimeStateRule("state_stressed", 1.0, None),
            ),
        ),
    )


def context_spec(**overrides: object) -> ContextResearchSpec:
    values: dict[str, object] = {
        "specification_id": "context-h20",
        "definition_version": "v1",
        "horizon": Horizon.H20,
        "base_alpha_specification_id": "alpha-h20-base",
        "base_alpha_definition_version": "v1",
        "context_protocol_id": "context-protocol-v1",
        "universe_rule_version": "universe-v1",
        "hypothesis": "Explicit regime and interaction context may explain Alpha stability.",
        "success_criteria": "Improve OOS robustness without hidden factor mutation.",
        "preregistered_at": PREDICTION - timedelta(days=30),
        "regime_dimensions": regime_dimensions(),
        "contradiction_rules": (
            ContradictionRule(
                rule_id="value-vs-momentum",
                left_admission_id=VALUE.admission_id,
                right_admission_id=MOMENTUM.admission_id,
                minimum_absolute_signal=0.25,
                required_regime_states=(("risk_axis", "state_stressed"),),
            ),
        ),
        "interaction_rules": (
            InteractionRule(
                rule_id="value-x-momentum",
                left_admission_id=VALUE.admission_id,
                right_admission_id=MOMENTUM.admission_id,
                required_regime_states=(("macro_axis", "state_high"),),
            ),
        ),
    }
    values.update(overrides)
    return ContextResearchSpec(**values)  # type: ignore[arg-type]


def observation(
    dimension_id: str,
    raw_value: float,
    *,
    age_days: int = 1,
    protocol: str = "context-protocol-v1",
) -> RegimeObservation:
    end = PREDICTION - timedelta(days=age_days)
    return RegimeObservation(
        observation_id=f"obs-{dimension_id}",
        dimension_id=dimension_id,
        context_protocol_id=protocol,
        raw_value=raw_value,
        window_start=end - timedelta(days=30),
        window_end=end,
        available_at=end + timedelta(hours=1),
        source_snapshot_id=f"source-{dimension_id}",
    )


def base_weights() -> list[AlphaFactorWeight]:
    return [
        AlphaFactorWeight(VALUE, 1.0),
        AlphaFactorWeight(MOMENTUM, 1.0),
    ]


def factor_signals(
    value_signal: float = 0.8,
    momentum_signal: float = -0.6,
) -> list[ContextFactorSignal]:
    return [
        ContextFactorSignal(VALUE, value_signal),
        ContextFactorSignal(MOMENTUM, momentum_signal),
    ]


def test_regime_state_intervals_must_be_non_overlapping_and_canonical() -> None:
    with pytest.raises(ValueError, match="overlap"):
        RegimeDimensionSpec(
            dimension_id="axis",
            max_age_days=10,
            state_rules=(
                RegimeStateRule("a", None, 1.0),
                RegimeStateRule("b", 0.5, None),
            ),
        )

    with pytest.raises(ValueError, match="canonical"):
        RegimeDimensionSpec(
            dimension_id="axis",
            max_age_days=10,
            state_rules=(
                RegimeStateRule("high", 0.0, None),
                RegimeStateRule("low", None, 0.0),
            ),
        )


def test_context_registry_rejects_conflicting_rewrite() -> None:
    registry = ContextResearchRegistry()
    item = context_spec()
    registry.register(item)
    registry.register(item)
    with pytest.raises(ValueError, match="conflicting"):
        registry.register(context_spec(success_criteria="changed after results"))


def test_future_regime_evidence_is_rejected() -> None:
    future_end = PREDICTION + timedelta(days=1)
    future = RegimeObservation(
        observation_id="future",
        dimension_id="macro_axis",
        context_protocol_id="context-protocol-v1",
        raw_value=1.0,
        window_start=PREDICTION - timedelta(days=10),
        window_end=future_end,
        available_at=future_end + timedelta(hours=1),
        source_snapshot_id="future-source",
    )
    with pytest.raises(ValueError, match="future regime"):
        evaluate_context_research(
            specification=context_spec(),
            base_alpha_specification=base_spec(),
            base_weights=base_weights(),
            regime_observations=[future, observation("risk_axis", 2.0)],
            factor_signals=factor_signals(),
            prediction_timestamp=PREDICTION,
        )


def test_stale_regime_causes_context_abstention_not_neutral_state() -> None:
    result = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", 1.0),
            observation("risk_axis", 2.0, age_days=11),
        ],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    assert result.status is ContextRunStatus.ABSTAIN_INSUFFICIENT_REGIME
    by_dimension = {item.dimension_id: item for item in result.regime_results}
    assert by_dimension["risk_axis"].availability is RegimeAvailability.STALE
    assert by_dimension["risk_axis"].state_id is None
    assert result.contradiction_results == ()
    assert result.interaction_results == ()


def test_missing_regime_dimension_causes_context_abstention() -> None:
    result = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[observation("macro_axis", 1.0)],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    assert result.status is ContextRunStatus.ABSTAIN_INSUFFICIENT_REGIME
    by_dimension = {item.dimension_id: item for item in result.regime_results}
    assert by_dimension["risk_axis"].availability is RegimeAvailability.MISSING


def test_protocol_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="protocol mismatch"):
        evaluate_context_research(
            specification=context_spec(),
            base_alpha_specification=base_spec(),
            base_weights=base_weights(),
            regime_observations=[
                observation("macro_axis", 1.0, protocol="post-hoc"),
                observation("risk_axis", 2.0),
            ],
            factor_signals=factor_signals(),
            prediction_timestamp=PREDICTION,
        )


def test_post_hoc_context_spec_is_rejected() -> None:
    with pytest.raises(ValueError, match="preregistered"):
        evaluate_context_research(
            specification=context_spec(
                preregistered_at=PREDICTION + timedelta(seconds=1)
            ),
            base_alpha_specification=base_spec(),
            base_weights=base_weights(),
            regime_observations=[
                observation("macro_axis", 1.0),
                observation("risk_axis", 2.0),
            ],
            factor_signals=factor_signals(),
            prediction_timestamp=PREDICTION,
        )


def test_missing_required_factor_signal_causes_plan_level_abstention() -> None:
    result = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", 1.0),
            observation("risk_axis", 2.0),
        ],
        factor_signals=[ContextFactorSignal(VALUE, 0.8)],
        prediction_timestamp=PREDICTION,
    )
    assert result.status is ContextRunStatus.ABSTAIN_INSUFFICIENT_FACTOR_SIGNALS
    assert result.missing_admission_ids == (MOMENTUM.admission_id,)


def test_contradiction_is_explicit_magnitude_and_regime_conditioned() -> None:
    result = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", 1.0),
            observation("risk_axis", 2.0),
        ],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    assert result.status is ContextRunStatus.EVALUATED
    contradiction = result.contradiction_results[0]
    assert contradiction.regime_condition_met is True
    assert contradiction.is_contradiction is True
    assert contradiction.left_signal == pytest.approx(0.8)
    assert contradiction.right_signal == pytest.approx(-0.6)


def test_contradiction_does_not_activate_when_regime_condition_is_false() -> None:
    result = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", 1.0),
            observation("risk_axis", 0.5),
        ],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    contradiction = result.contradiction_results[0]
    assert contradiction.regime_condition_met is False
    assert contradiction.is_contradiction is False


def test_interaction_is_explicit_product_and_regime_conditioned() -> None:
    active = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", 1.0),
            observation("risk_axis", 2.0),
        ],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    interaction = active.interaction_results[0]
    assert interaction.state is InteractionState.ACTIVE
    assert interaction.interaction_value == pytest.approx(-0.48)

    inactive = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", -1.0),
            observation("risk_axis", 2.0),
        ],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    interaction = inactive.interaction_results[0]
    assert interaction.state is InteractionState.INACTIVE_REGIME
    assert interaction.interaction_value is None


def test_rules_cannot_reference_factor_outside_base_alpha_plan() -> None:
    unknown_rule = InteractionRule(
        rule_id="bad",
        left_admission_id=VALUE.admission_id,
        right_admission_id="adm-not-in-base",
    )
    with pytest.raises(ValueError, match="outside base Alpha"):
        evaluate_context_research(
            specification=context_spec(interaction_rules=(unknown_rule,)),
            base_alpha_specification=base_spec(),
            base_weights=base_weights(),
            regime_observations=[
                observation("macro_axis", 1.0),
                observation("risk_axis", 2.0),
            ],
            factor_signals=factor_signals(),
            prediction_timestamp=PREDICTION,
        )


def test_output_contains_no_alpha_mutation_portfolio_or_confidence_fields() -> None:
    result = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", 1.0),
            observation("risk_axis", 2.0),
        ],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    assert not hasattr(result, "adjusted_alpha")
    assert not hasattr(result, "portfolio_weight")
    assert not hasattr(result, "confidence")


def test_fixed_inputs_are_deterministic_independent_of_input_order() -> None:
    first = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=base_weights(),
        regime_observations=[
            observation("macro_axis", 1.0),
            observation("risk_axis", 2.0),
        ],
        factor_signals=factor_signals(),
        prediction_timestamp=PREDICTION,
    )
    second = evaluate_context_research(
        specification=context_spec(),
        base_alpha_specification=base_spec(),
        base_weights=list(reversed(base_weights())),
        regime_observations=list(
            reversed(
                [
                    observation("macro_axis", 1.0),
                    observation("risk_axis", 2.0),
                ]
            )
        ),
        factor_signals=list(reversed(factor_signals())),
        prediction_timestamp=PREDICTION,
    )
    assert first == second
