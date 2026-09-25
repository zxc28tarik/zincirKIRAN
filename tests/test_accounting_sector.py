from __future__ import annotations

import pytest

from zincir_kiran.accounting import (
    AccountingComparisonError,
    AccountingContext,
    ComparabilityDecision,
    compare_accounting_contexts,
    require_comparable,
)
from zincir_kiran.applicability import (
    ApplicabilityDecision,
    ApplicabilityRegistry,
    FeatureApplicabilityError,
)


def context(
    *,
    standard: str | None = "TFRS",
    inflation_adjusted: bool | None = True,
) -> AccountingContext:
    return AccountingContext(
        reporting_standard=standard,
        inflation_adjusted=inflation_adjusted,
    )


def test_matching_known_accounting_regimes_are_comparable() -> None:
    result = compare_accounting_contexts(context(), context())
    assert result.decision is ComparabilityDecision.COMPARABLE


def test_pre_post_inflation_adjustment_mismatch_is_blocked() -> None:
    result = compare_accounting_contexts(
        context(inflation_adjusted=False),
        context(inflation_adjusted=True),
    )
    assert result.decision is ComparabilityDecision.BLOCKED
    assert "inflation-adjustment" in result.reason


def test_reporting_standard_mismatch_is_blocked() -> None:
    result = compare_accounting_contexts(
        context(standard="TFRS"),
        context(standard="IFRS"),
    )
    assert result.decision is ComparabilityDecision.BLOCKED


@pytest.mark.parametrize(
    ("standard", "inflation_adjusted"),
    [(None, True), ("TFRS", None)],
)
def test_missing_accounting_metadata_is_undecided(
    standard: str | None,
    inflation_adjusted: bool | None,
) -> None:
    result = compare_accounting_contexts(
        context(),
        context(standard=standard, inflation_adjusted=inflation_adjusted),
    )
    assert result.decision is ComparabilityDecision.UNDECIDED


def test_noncomparable_context_cannot_be_used_silently() -> None:
    with pytest.raises(AccountingComparisonError, match="BLOCKED"):
        require_comparable(
            context(inflation_adjusted=False),
            context(inflation_adjusted=True),
        )


def test_applicability_defaults_to_undecided_not_applies() -> None:
    registry = ApplicabilityRegistry()
    assert (
        registry.decision_for("EV_EBITDA", "BANK")
        is ApplicabilityDecision.UNDECIDED
    )


def test_explicit_not_applicable_cannot_enter_scoring() -> None:
    registry = ApplicabilityRegistry()
    registry.set_decision(
        "EV_EBITDA",
        "BANK",
        ApplicabilityDecision.DOES_NOT_APPLY,
    )

    with pytest.raises(FeatureApplicabilityError, match="DOES_NOT_APPLY"):
        registry.require_applicable("EV_EBITDA", "BANK")


def test_undecided_cannot_enter_scoring() -> None:
    registry = ApplicabilityRegistry()
    with pytest.raises(FeatureApplicabilityError, match="UNDECIDED"):
        registry.require_applicable("FCF_EV", "INSURER")


def test_explicit_applicable_feature_passes_gate() -> None:
    registry = ApplicabilityRegistry()
    registry.set_decision(
        "BOOK_TO_PRICE",
        "BANK",
        ApplicabilityDecision.APPLIES,
    )
    registry.require_applicable("BOOK_TO_PRICE", "BANK")
