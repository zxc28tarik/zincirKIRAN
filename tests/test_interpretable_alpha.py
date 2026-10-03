import math

import pytest

from zincir_kiran.baselines import Horizon
from zincir_kiran.interpretable_alpha import (
    AdmissionDecision,
    AdmittedFactorInput,
    FactorAdmission,
    FactorAdmissionRegistry,
    alpha_field_name,
    require_admitted_factor_inputs,
)


def admission(**overrides: object) -> FactorAdmission:
    values: dict[str, object] = {
        "admission_id": "adm-book-h20-v1",
        "factor_id": "book_to_price",
        "factor_definition_version": "v1",
        "horizon": Horizon.H20,
        "decision": AdmissionDecision.ADMITTED,
        "factor_lab_experiment_id": "exp-book-h20-v1",
        "decorrelation_run_id": "decor-h20-v1",
        "decorrelation_component_id": "component-1",
        "rationale": "Explicit research admission after Factor Lab and de-correlation.",
    }
    values.update(overrides)
    return FactorAdmission(**values)  # type: ignore[arg-type]


def test_alpha_fields_are_horizon_specific_and_locked() -> None:
    assert alpha_field_name(Horizon.H20) == "Alpha20"
    assert alpha_field_name(Horizon.H60) == "Alpha60"
    assert alpha_field_name(Horizon.H120) == "Alpha120"
    assert alpha_field_name(Horizon.H252) == "Alpha252"


def test_admission_requires_factor_lab_and_decorrelation_provenance() -> None:
    item = admission()
    assert item.factor_lab_experiment_id == "exp-book-h20-v1"
    assert item.decorrelation_run_id == "decor-h20-v1"
    assert item.decorrelation_component_id == "component-1"


def test_only_explicitly_admitted_factor_can_enter_alpha_input() -> None:
    admitted = AdmittedFactorInput(admission=admission(), signal_value=0.70)
    result = require_admitted_factor_inputs([admitted], horizon=Horizon.H20)
    assert result == (admitted,)


@pytest.mark.parametrize(
    "decision",
    [AdmissionDecision.REJECTED, AdmissionDecision.UNDECIDED],
)
def test_non_admitted_factor_is_blocked(decision: AdmissionDecision) -> None:
    item = AdmittedFactorInput(
        admission=admission(decision=decision),
        signal_value=0.40,
    )
    with pytest.raises(ValueError, match="not admitted"):
        require_admitted_factor_inputs([item], horizon=Horizon.H20)


def test_admission_for_other_horizon_cannot_leak_into_alpha() -> None:
    item = AdmittedFactorInput(
        admission=admission(horizon=Horizon.H60),
        signal_value=0.40,
    )
    with pytest.raises(ValueError, match="horizon"):
        require_admitted_factor_inputs([item], horizon=Horizon.H20)


@pytest.mark.parametrize("value", [None, math.nan, math.inf, -math.inf])
def test_missing_or_nonfinite_signal_is_not_neutralized(value: float | None) -> None:
    item = AdmittedFactorInput(admission=admission(), signal_value=value)
    with pytest.raises(ValueError, match="finite signal_value"):
        require_admitted_factor_inputs([item], horizon=Horizon.H20)


def test_duplicate_factor_definition_is_rejected() -> None:
    first = AdmittedFactorInput(admission=admission(), signal_value=0.20)
    second = AdmittedFactorInput(
        admission=admission(admission_id="adm-book-h20-v2"),
        signal_value=0.30,
    )
    with pytest.raises(ValueError, match="duplicate admitted factor definition"):
        require_admitted_factor_inputs([first, second], horizon=Horizon.H20)


def test_admitted_input_order_is_deterministic() -> None:
    book = AdmittedFactorInput(admission=admission(), signal_value=0.20)
    momentum = AdmittedFactorInput(
        admission=admission(
            admission_id="adm-mom-h20-v1",
            factor_id="momentum_12_1",
            factor_lab_experiment_id="exp-mom-h20-v1",
            decorrelation_component_id="component-2",
        ),
        signal_value=0.80,
    )
    result = require_admitted_factor_inputs(
        [momentum, book],
        horizon=Horizon.H20,
    )
    assert tuple(item.admission.factor_id for item in result) == (
        "book_to_price",
        "momentum_12_1",
    )


def test_factor_admission_registry_rejects_conflicting_rewrite() -> None:
    registry = FactorAdmissionRegistry()
    registry.register(admission())
    registry.register(admission())
    with pytest.raises(ValueError, match="conflicting"):
        registry.register(admission(decision=AdmissionDecision.REJECTED))

def test_same_decorrelation_component_cannot_vote_twice() -> None:
    first = AdmittedFactorInput(
        admission=admission(
            admission_id="adm-mom-12-1",
            factor_id="momentum_12_1",
            factor_lab_experiment_id="exp-mom-12-1",
            decorrelation_run_id="decor-h20-v1",
            decorrelation_component_id="component-momentum",
        ),
        signal_value=0.70,
    )
    second = AdmittedFactorInput(
        admission=admission(
            admission_id="adm-mom-6-1",
            factor_id="momentum_6_1",
            factor_lab_experiment_id="exp-mom-6-1",
            decorrelation_run_id="decor-h20-v1",
            decorrelation_component_id="component-momentum",
        ),
        signal_value=0.60,
    )

    with pytest.raises(ValueError, match="same de-correlation component"):
        require_admitted_factor_inputs([first, second], horizon=Horizon.H20)


def test_different_components_can_each_contribute_one_vote() -> None:
    value = AdmittedFactorInput(
        admission=admission(
            admission_id="adm-value",
            factor_id="book_to_price",
            factor_lab_experiment_id="exp-value",
            decorrelation_run_id="decor-h20-v1",
            decorrelation_component_id="component-value",
        ),
        signal_value=0.40,
    )
    momentum = AdmittedFactorInput(
        admission=admission(
            admission_id="adm-momentum",
            factor_id="momentum_12_1",
            factor_lab_experiment_id="exp-momentum",
            decorrelation_run_id="decor-h20-v1",
            decorrelation_component_id="component-momentum",
        ),
        signal_value=0.80,
    )

    result = require_admitted_factor_inputs([momentum, value], horizon=Horizon.H20)

    assert tuple(item.admission.factor_id for item in result) == (
        "book_to_price",
        "momentum_12_1",
    )


def test_same_component_label_in_different_runs_does_not_false_collide() -> None:
    first = AdmittedFactorInput(
        admission=admission(
            admission_id="adm-a",
            factor_id="factor_a",
            factor_lab_experiment_id="exp-a",
            decorrelation_run_id="decor-run-a",
            decorrelation_component_id="component-1",
        ),
        signal_value=0.10,
    )
    second = AdmittedFactorInput(
        admission=admission(
            admission_id="adm-b",
            factor_id="factor_b",
            factor_lab_experiment_id="exp-b",
            decorrelation_run_id="decor-run-b",
            decorrelation_component_id="component-1",
        ),
        signal_value=0.20,
    )

    result = require_admitted_factor_inputs([first, second], horizon=Horizon.H20)
    assert len(result) == 2
