"""Accounting-regime comparability guards for financial features."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RestatementStatus(StrEnum):
    ORIGINAL = "ORIGINAL"
    RESTATED = "RESTATED"
    UNKNOWN = "UNKNOWN"


class ComparabilityDecision(StrEnum):
    COMPARABLE = "COMPARABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNDECIDED = "UNDECIDED"


@dataclass(frozen=True)
class AccountingContext:
    reporting_standard: str | None
    inflation_adjusted: bool | None
    restatement_status: RestatementStatus = RestatementStatus.UNKNOWN
    original_period: str | None = None

    @property
    def is_decidable(self) -> bool:
        return (
            bool(self.reporting_standard)
            and self.inflation_adjusted is not None
            and self.restatement_status is not RestatementStatus.UNKNOWN
        )


def compare_accounting_context(
    left: AccountingContext,
    right: AccountingContext,
) -> ComparabilityDecision:
    """Decide whether two financial facts are safe to compare automatically."""
    if not left.is_decidable or not right.is_decidable:
        return ComparabilityDecision.UNDECIDED

    if left.reporting_standard != right.reporting_standard:
        return ComparabilityDecision.INCOMPATIBLE
    if left.inflation_adjusted != right.inflation_adjusted:
        return ComparabilityDecision.INCOMPATIBLE
    if left.restatement_status != right.restatement_status:
        return ComparabilityDecision.INCOMPATIBLE

    return ComparabilityDecision.COMPARABLE


def require_comparable(left: AccountingContext, right: AccountingContext) -> None:
    """Block feature calculation unless accounting contexts are explicitly comparable."""
    decision = compare_accounting_context(left, right)
    if decision is not ComparabilityDecision.COMPARABLE:
        raise ValueError(f"accounting contexts are not comparable: {decision.value}")
