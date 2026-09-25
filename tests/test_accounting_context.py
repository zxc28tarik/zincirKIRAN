from zincir_kiran.accounting import (
    AccountingContext,
    ComparabilityDecision,
    RestatementStatus,
    compare_accounting_context,
    require_comparable,
)


def context(
    *,
    standard: str | None = "TFRS",
    inflation: bool | None = True,
    restatement: RestatementStatus = RestatementStatus.RESTATED,
) -> AccountingContext:
    return AccountingContext(
        reporting_standard=standard,
        inflation_adjusted=inflation,
        restatement_status=restatement,
    )


def test_same_known_accounting_regime_is_comparable() -> None:
    assert compare_accounting_context(context(), context()) is ComparabilityDecision.COMPARABLE


def test_inflation_adjustment_mismatch_is_blocked() -> None:
    result = compare_accounting_context(context(inflation=True), context(inflation=False))
    assert result is ComparabilityDecision.INCOMPATIBLE


def test_reporting_standard_mismatch_is_blocked() -> None:
    result = compare_accounting_context(context(standard="TFRS"), context(standard="BOBİ FRS"))
    assert result is ComparabilityDecision.INCOMPATIBLE


def test_restatement_mismatch_is_blocked_by_default() -> None:
    result = compare_accounting_context(
        context(restatement=RestatementStatus.RESTATED),
        context(restatement=RestatementStatus.ORIGINAL),
    )
    assert result is ComparabilityDecision.INCOMPATIBLE


def test_missing_regime_metadata_is_undecided() -> None:
    assert (
        compare_accounting_context(context(standard=None), context())
        is ComparabilityDecision.UNDECIDED
    )
    assert (
        compare_accounting_context(context(inflation=None), context())
        is ComparabilityDecision.UNDECIDED
    )
    assert (
        compare_accounting_context(
            context(restatement=RestatementStatus.UNKNOWN),
            context(),
        )
        is ComparabilityDecision.UNDECIDED
    )


def test_undecided_context_cannot_enter_feature_calculation() -> None:
    try:
        require_comparable(context(standard=None), context())
    except ValueError as exc:
        assert "UNDECIDED" in str(exc)
    else:
        raise AssertionError("UNDECIDED accounting context entered feature calculation")
