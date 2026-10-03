import pytest

from zincir_kiran.accounting import ComparabilityDecision
from zincir_kiran.alpha_aggregation import AlphaAggregationSpec
from zincir_kiran.alpha_engine import (
    AlphaExecutionStatus,
    AlphaFactorWeight,
    AlphaSignalObservation,
    SignalAvailability,
    execute_interpretable_alpha,
    validate_weight_plan,
)
from zincir_kiran.applicability import Applicability
from zincir_kiran.baselines import Horizon
from zincir_kiran.interpretable_alpha import AdmissionDecision, FactorAdmission


def admission(
    factor_id: str,
    component_no: int,
    *,
    admission_id: str | None = None,
    horizon: Horizon = Horizon.H20,
    run_id: str = "decor-h20-v1",
) -> FactorAdmission:
    chosen_id = admission_id or f"adm-{factor_id}"
    return FactorAdmission(
        admission_id=chosen_id,
        factor_id=factor_id,
        factor_definition_version="v1",
        horizon=horizon,
        decision=AdmissionDecision.ADMITTED,
        factor_lab_experiment_id=f"exp-{factor_id}",
        decorrelation_run_id=run_id,
        decorrelation_component_no=component_no,
        rationale="test admission",
    )


def spec(**overrides: object) -> AlphaAggregationSpec:
    values: dict[str, object] = {
        "specification_id": "alpha-h20",
        "definition_version": "v1",
        "horizon": Horizon.H20,
        "aggregation_rule_id": "WEIGHTED_ABS_MEAN",
        "normalization_rule_id": "TEST_NORMALIZATION_V1",
        "weight_policy_id": "TEST_EXPLICIT_WEIGHTS_V1",
        "coverage_rule_id": "ABS_WEIGHT_COVERAGE",
        "parameters": (("minimum_coverage", "0.75"),),
    }
    values.update(overrides)
    return AlphaAggregationSpec(**values)  # type: ignore[arg-type]


def available(adm: FactorAdmission, raw: float, normalized: float) -> AlphaSignalObservation:
    return AlphaSignalObservation(
        admission=adm,
        availability=SignalAvailability.AVAILABLE,
        applicability=Applicability.APPLIES,
        accounting_comparability=ComparabilityDecision.COMPARABLE,
        raw_signal_value=raw,
        normalization_rule_id="TEST_NORMALIZATION_V1",
        normalized_value=normalized,
    )


def unavailable(adm: FactorAdmission, state: SignalAvailability) -> AlphaSignalObservation:
    if state is SignalAvailability.NOT_APPLICABLE:
        applicability = Applicability.DOES_NOT_APPLY
        accounting = ComparabilityDecision.COMPARABLE
    elif state is SignalAvailability.UNDECIDED:
        applicability = Applicability.UNDECIDED
        accounting = ComparabilityDecision.COMPARABLE
    elif state is SignalAvailability.ACCOUNTING_INCOMPATIBLE:
        applicability = Applicability.APPLIES
        accounting = ComparabilityDecision.INCOMPATIBLE
    else:
        applicability = Applicability.APPLIES
        accounting = ComparabilityDecision.COMPARABLE
    return AlphaSignalObservation(
        admission=adm,
        availability=state,
        applicability=applicability,
        accounting_comparability=accounting,
    )


def test_weight_plan_rejects_duplicate_decorrelation_vote() -> None:
    first = admission("momentum_12_1", 1)
    second = admission("momentum_6_1", 1)
    with pytest.raises(ValueError, match="duplicate de-correlation vote"):
        validate_weight_plan(
            [AlphaFactorWeight(first, 1.0), AlphaFactorWeight(second, 1.0)],
            horizon=Horizon.H20,
        )


def test_weight_plan_rejects_zero_or_nonfinite_weight() -> None:
    adm = admission("value", 1)
    for weight in (0.0, float("inf"), float("nan")):
        with pytest.raises(ValueError, match="finite and non-zero"):
            AlphaFactorWeight(adm, weight)


def test_full_coverage_produces_auditable_weighted_abs_mean() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    result = execute_interpretable_alpha(
        security_id="SEC-1",
        specification=spec(),
        weights=[
            AlphaFactorWeight(value, 2.0),
            AlphaFactorWeight(momentum, 1.0),
        ],
        observations=[
            available(momentum, 0.8, 0.5),
            available(value, 0.2, -0.25),
        ],
    )

    assert result.status is AlphaExecutionStatus.SCORED
    assert result.coverage == pytest.approx(1.0)
    assert result.planned_factor_count == 2
    assert result.available_factor_count == 2
    assert result.alpha_value == pytest.approx(0.0)
    assert tuple(item.factor_id for item in result.contributions) == ("momentum", "value")
    by_factor = {item.factor_id: item for item in result.contributions}
    assert by_factor["value"].weighted_contribution == pytest.approx(-0.5)
    assert by_factor["momentum"].weighted_contribution == pytest.approx(0.5)
    assert result.unavailable_inputs == ()


def test_insufficient_weight_coverage_abstains_without_neutral_fill() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    result = execute_interpretable_alpha(
        security_id="SEC-1",
        specification=spec(parameters=(("minimum_coverage", "0.80"),)),
        weights=[
            AlphaFactorWeight(value, 3.0),
            AlphaFactorWeight(momentum, 1.0),
        ],
        observations=[
            unavailable(value, SignalAvailability.MISSING),
            available(momentum, 0.8, 0.5),
        ],
    )

    assert result.status is AlphaExecutionStatus.ABSTAIN_INSUFFICIENT_COVERAGE
    assert result.alpha_value is None
    assert result.coverage == pytest.approx(0.25)
    assert result.planned_factor_count == 2
    assert result.available_factor_count == 1
    assert tuple(item.availability for item in result.unavailable_inputs) == (
        SignalAvailability.MISSING,
    )


@pytest.mark.parametrize(
    "state",
    [SignalAvailability.MISSING, SignalAvailability.NOT_APPLICABLE, SignalAvailability.UNDECIDED],
)
def test_unavailable_states_cannot_carry_hidden_numeric_values(state: SignalAvailability) -> None:
    adm = admission("value", 1)
    with pytest.raises(ValueError, match="cannot carry"):
        AlphaSignalObservation(
            admission=adm,
            availability=state,
            applicability=(
                Applicability.DOES_NOT_APPLY
                if state is SignalAvailability.NOT_APPLICABLE
                else Applicability.UNDECIDED
                if state is SignalAvailability.UNDECIDED
                else Applicability.APPLIES
            ),
            accounting_comparability=ComparabilityDecision.COMPARABLE,
            raw_signal_value=0.0,
            normalized_value=0.0,
            normalization_rule_id="TEST_NORMALIZATION_V1",
        )


def test_normalization_provenance_must_match_specification() -> None:
    adm = admission("value", 1)
    observation = AlphaSignalObservation(
        admission=adm,
        availability=SignalAvailability.AVAILABLE,
        applicability=Applicability.APPLIES,
        accounting_comparability=ComparabilityDecision.COMPARABLE,
        raw_signal_value=0.2,
        normalization_rule_id="OTHER_NORMALIZATION",
        normalized_value=0.1,
    )
    with pytest.raises(ValueError, match="normalization"):
        execute_interpretable_alpha(
            security_id="SEC-1",
            specification=spec(),
            weights=[AlphaFactorWeight(adm, 1.0)],
            observations=[observation],
        )


def test_every_planned_factor_requires_explicit_availability_observation() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    with pytest.raises(ValueError, match="every planned admission"):
        execute_interpretable_alpha(
            security_id="SEC-1",
            specification=spec(),
            weights=[AlphaFactorWeight(value, 1.0), AlphaFactorWeight(momentum, 1.0)],
            observations=[available(value, 0.2, 0.1)],
        )


def test_factor_count_coverage_is_supported_without_selecting_it_for_production() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    result = execute_interpretable_alpha(
        security_id="SEC-1",
        specification=spec(
            coverage_rule_id="FACTOR_COUNT_COVERAGE",
            parameters=(("minimum_coverage", "0.50"),),
        ),
        weights=[AlphaFactorWeight(value, 9.0), AlphaFactorWeight(momentum, 1.0)],
        observations=[
            unavailable(value, SignalAvailability.NOT_APPLICABLE),
            available(momentum, 0.8, 0.5),
        ],
    )
    assert result.status is AlphaExecutionStatus.SCORED
    assert result.coverage == pytest.approx(0.5)


def test_weighted_sum_and_weighted_abs_mean_are_distinct_supported_primitives() -> None:
    value = admission("value", 1)
    observation = available(value, 0.2, 0.5)
    weights = [AlphaFactorWeight(value, 2.0)]

    summed = execute_interpretable_alpha(
        security_id="SEC-1",
        specification=spec(aggregation_rule_id="WEIGHTED_SUM"),
        weights=weights,
        observations=[observation],
    )
    meaned = execute_interpretable_alpha(
        security_id="SEC-1",
        specification=spec(aggregation_rule_id="WEIGHTED_ABS_MEAN"),
        weights=weights,
        observations=[observation],
    )
    assert summed.alpha_value == pytest.approx(1.0)
    assert meaned.alpha_value == pytest.approx(0.5)


def test_execution_is_deterministic_for_fixed_inputs() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    weights = [AlphaFactorWeight(momentum, 1.0), AlphaFactorWeight(value, 2.0)]
    observations = [available(value, 0.2, -0.25), available(momentum, 0.8, 0.5)]
    first = execute_interpretable_alpha(
        security_id="SEC-1", specification=spec(), weights=weights, observations=observations
    )
    second = execute_interpretable_alpha(
        security_id="SEC-1",
        specification=spec(),
        weights=list(reversed(weights)),
        observations=list(reversed(observations)),
    )
    assert first == second


def test_result_contract_contains_no_portfolio_or_confidence_fields() -> None:
    adm = admission("value", 1)
    result = execute_interpretable_alpha(
        security_id="SEC-1",
        specification=spec(),
        weights=[AlphaFactorWeight(adm, 1.0)],
        observations=[available(adm, 0.2, 0.1)],
    )
    assert not hasattr(result, "portfolio_weight")
    assert not hasattr(result, "position_size")
    assert not hasattr(result, "confidence")

def test_available_signal_requires_applicability_and_accounting_gates() -> None:
    adm = admission("value", 1)
    with pytest.raises(ValueError, match="applicability APPLIES"):
        AlphaSignalObservation(
            admission=adm,
            availability=SignalAvailability.AVAILABLE,
            applicability=Applicability.UNDECIDED,
            accounting_comparability=ComparabilityDecision.COMPARABLE,
            raw_signal_value=0.2,
            normalization_rule_id="TEST_NORMALIZATION_V1",
            normalized_value=0.1,
        )

    with pytest.raises(ValueError, match="accounting COMPARABLE"):
        AlphaSignalObservation(
            admission=adm,
            availability=SignalAvailability.AVAILABLE,
            applicability=Applicability.APPLIES,
            accounting_comparability=ComparabilityDecision.INCOMPATIBLE,
            raw_signal_value=0.2,
            normalization_rule_id="TEST_NORMALIZATION_V1",
            normalized_value=0.1,
        )


def test_accounting_incompatible_is_explicit_unavailable_state() -> None:
    adm = admission("value", 1)
    observation = unavailable(adm, SignalAvailability.ACCOUNTING_INCOMPATIBLE)
    assert observation.accounting_comparability is ComparabilityDecision.INCOMPATIBLE
    assert observation.normalized_value is None
