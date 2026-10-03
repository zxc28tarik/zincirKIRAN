import pytest

from zincir_kiran.alpha_aggregation import AlphaAggregationRegistry, AlphaAggregationSpec
from zincir_kiran.baselines import Horizon


def spec(**overrides: object) -> AlphaAggregationSpec:
    values: dict[str, object] = {
        "specification_id": "alpha-h20-spec",
        "definition_version": "v1",
        "horizon": Horizon.H20,
        "aggregation_rule_id": "RULE_TO_BE_SELECTED_BY_EVIDENCE",
        "normalization_rule_id": "NORMALIZATION_TO_BE_SELECTED_BY_EVIDENCE",
        "weight_policy_id": "WEIGHTS_TO_BE_SELECTED_BY_EVIDENCE",
        "coverage_rule_id": "COVERAGE_TO_BE_SELECTED_BY_EVIDENCE",
        "parameters": (
            ("note", "contract-only"),
        ),
    }
    values.update(overrides)
    return AlphaAggregationSpec(**values)  # type: ignore[arg-type]


def test_aggregation_spec_is_horizon_specific() -> None:
    item = spec()
    assert item.horizon is Horizon.H20


def test_aggregation_spec_requires_all_rule_identifiers() -> None:
    for field in (
        "aggregation_rule_id",
        "normalization_rule_id",
        "weight_policy_id",
        "coverage_rule_id",
    ):
        with pytest.raises(ValueError, match=field):
            spec(**{field: ""})


def test_parameters_must_be_unique_and_sorted() -> None:
    with pytest.raises(ValueError, match="unique and sorted"):
        spec(parameters=(("z", "1"), ("a", "2")))


def test_registry_is_idempotent_for_identical_specification() -> None:
    registry = AlphaAggregationRegistry()
    item = spec()
    registry.register(item)
    registry.register(item)
    assert registry.get(item.specification_id, item.definition_version) == item


def test_registry_rejects_conflicting_rewrite_of_same_version() -> None:
    registry = AlphaAggregationRegistry()
    registry.register(spec())

    with pytest.raises(ValueError, match="conflicting"):
        registry.register(
            spec(weight_policy_id="CHANGED_AFTER_RESULTS")
        )


def test_new_version_may_define_a_different_rule_without_rewriting_history() -> None:
    registry = AlphaAggregationRegistry()
    first = spec()
    second = spec(
        definition_version="v2",
        aggregation_rule_id="A_DIFFERENT_PRE_REGISTERED_RULE",
    )
    registry.register(first)
    registry.register(second)

    assert registry.get("alpha-h20-spec", "v1") == first
    assert registry.get("alpha-h20-spec", "v2") == second
