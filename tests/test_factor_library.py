import pytest

from zincir_kiran.factor_library import (
    CandidateFactorRegistry,
    EconomicFamily,
    EvidenceStatus,
    ExpectedDirection,
    FactorDefinition,
    FactorStage,
    MissingFactorInputError,
    require_factor_inputs,
)


def definition(**overrides: object) -> FactorDefinition:
    values: dict[str, object] = {
        "factor_id": "book_to_price",
        "definition_version": "v1",
        "economic_family": EconomicFamily.VALUE,
        "economic_concept_key": "book_value_yield",
        "specification": "book_equity / market_cap",
        "required_fields": ("book_equity", "market_cap"),
        "expected_direction": ExpectedDirection.HIGHER_IS_BETTER,
    }
    values.update(overrides)
    return FactorDefinition(**values)  # type: ignore[arg-type]


def test_all_locked_economic_families_exist() -> None:
    assert {family.value for family in EconomicFamily} == {
        "VALUE",
        "PROFITABILITY",
        "QUALITY",
        "INVESTMENT_DISCIPLINE",
        "FUNDAMENTAL_ACCELERATION",
        "PRICE_MOMENTUM",
        "EARNINGS_MOMENTUM",
        "RISK",
        "LIQUIDITY",
        "SIZE_CONTROL",
    }


def test_new_factor_defaults_to_candidate_and_unreviewed() -> None:
    item = definition()
    assert item.stage is FactorStage.CANDIDATE
    assert item.evidence_status is EvidenceStatus.UNREVIEWED


def test_candidate_registry_rejects_premature_production_factor() -> None:
    registry = CandidateFactorRegistry()
    with pytest.raises(ValueError, match="only CANDIDATE"):
        registry.register(definition(stage=FactorStage.PRODUCTION))


def test_conflicting_factor_version_rewrite_is_rejected() -> None:
    registry = CandidateFactorRegistry()
    registry.register(definition())
    with pytest.raises(ValueError, match="conflicting"):
        registry.register(definition(specification="changed after results"))


def test_alternative_definitions_share_concept_without_becoming_extra_votes() -> None:
    registry = CandidateFactorRegistry()
    registry.register(definition(factor_id="book_to_price"))
    registry.register(
        definition(
            factor_id="book_to_market_alt",
            definition_version="v1",
            specification="tangible_book_equity / market_cap",
            required_fields=("market_cap", "tangible_book_equity"),
        )
    )
    assert len(registry.concept_members("book_value_yield")) == 2


def test_direction_may_remain_explicitly_undecided() -> None:
    item = definition(expected_direction=ExpectedDirection.UNDECIDED)
    assert item.expected_direction is ExpectedDirection.UNDECIDED


def test_missing_factor_input_is_rejected_not_neutralized() -> None:
    item = definition()
    with pytest.raises(MissingFactorInputError, match="book_equity"):
        require_factor_inputs(item, {"book_equity": None, "market_cap": 100})


def test_complete_factor_inputs_follow_declared_field_order() -> None:
    item = definition()
    assert require_factor_inputs(item, {"market_cap": 100, "book_equity": 40}) == (40, 100)
