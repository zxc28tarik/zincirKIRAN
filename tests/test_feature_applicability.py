import pytest

from zincir_kiran.applicability import Applicability, FeatureApplicabilityRegistry


def test_missing_applicability_is_undecided() -> None:
    registry = FeatureApplicabilityRegistry()
    assert (
        registry.get(feature_id="ev_to_ebitda", company_type="BANK")
        is Applicability.UNDECIDED
    )


def test_only_explicit_applies_can_enter_scoring() -> None:
    registry = FeatureApplicabilityRegistry()
    registry.register(
        feature_id="example_feature",
        company_type="EXAMPLE_TYPE",
        state=Applicability.APPLIES,
    )

    registry.require_scoring_allowed(
        feature_id="example_feature",
        company_type="EXAMPLE_TYPE",
    )


def test_not_applicable_and_undecided_are_never_neutralized() -> None:
    registry = FeatureApplicabilityRegistry()
    registry.register(
        feature_id="example_feature",
        company_type="TYPE_A",
        state=Applicability.DOES_NOT_APPLY,
    )

    with pytest.raises(ValueError, match="DOES_NOT_APPLY"):
        registry.require_scoring_allowed(feature_id="example_feature", company_type="TYPE_A")
    with pytest.raises(ValueError, match="UNDECIDED"):
        registry.require_scoring_allowed(feature_id="example_feature", company_type="TYPE_B")


def test_conflicting_registry_rewrite_is_rejected() -> None:
    registry = FeatureApplicabilityRegistry()
    registry.register(
        feature_id="example_feature",
        company_type="TYPE_A",
        state=Applicability.APPLIES,
    )

    with pytest.raises(ValueError, match="conflicting"):
        registry.register(
            feature_id="example_feature",
            company_type="TYPE_A",
            state=Applicability.DOES_NOT_APPLY,
        )
