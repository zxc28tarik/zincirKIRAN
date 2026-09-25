"""Accounting-regime comparability guards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComparabilityDecision(str, Enum):
    """Decision for whether two financial facts may be compared automatically."""

    COMPARABLE = "COMPARABLE"
    BLOCKED = "BLOCKED"
    UNDECIDED = "UNDECIDED"


@dataclass(frozen=True, slots=True)
class AccountingContext:
    """Accounting metadata required before cross-period comparisons."""

    reporting_standard: str | None
    inflation_adjusted: bool | None
    restatement_status: str | None = None
    original_period: str | None = None


@dataclass(frozen=True, slots=True)
class ComparabilityResult:
    decision: ComparabilityDecision
    reason: str


class AccountingComparisonError(ValueError):
    """Raised when code attempts to compare facts without a safe regime match."""


def _normalized_standard(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    return normalized or None


def compare_accounting_contexts(
    left: AccountingContext,
    right: AccountingContext,
) -> ComparabilityResult:
    """Return a conservative comparability decision.

    The first implementation deliberately refuses to infer TMS29/restatement
    equivalence. Explicit restatement bridges can be added later only when
    supported by source evidence and tests.
    """
    left_standard = _normalized_standard(left.reporting_standard)
    right_standard = _normalized_standard(right.reporting_standard)

    if left_standard is None or right_standard is None:
        return ComparabilityResult(
            ComparabilityDecision.UNDECIDED,
            "reporting_standard metadata is missing",
        )

    if left.inflation_adjusted is None or right.inflation_adjusted is None:
        return ComparabilityResult(
            ComparabilityDecision.UNDECIDED,
            "inflation_adjusted metadata is missing",
        )

    if left_standard != right_standard:
        return ComparabilityResult(
            ComparabilityDecision.BLOCKED,
            "reporting standards differ",
        )

    if left.inflation_adjusted != right.inflation_adjusted:
        return ComparabilityResult(
            ComparabilityDecision.BLOCKED,
            "inflation-adjustment regimes differ",
        )

    return ComparabilityResult(
        ComparabilityDecision.COMPARABLE,
        "accounting regimes match",
    )


def require_comparable(
    left: AccountingContext,
    right: AccountingContext,
) -> None:
    """Raise unless the comparison is explicitly safe."""
    result = compare_accounting_contexts(left, right)
    if result.decision is not ComparabilityDecision.COMPARABLE:
        raise AccountingComparisonError(
            f"{result.decision.value}: {result.reason}"
        )
