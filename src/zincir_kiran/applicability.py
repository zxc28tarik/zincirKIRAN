"""Explicit feature applicability by company type."""

from __future__ import annotations

from enum import Enum


class ApplicabilityDecision(str, Enum):
    APPLIES = "APPLIES"
    DOES_NOT_APPLY = "DOES_NOT_APPLY"
    UNDECIDED = "UNDECIDED"


class FeatureApplicabilityError(ValueError):
    """Raised when a feature is not explicitly approved for a company type."""


def _key(feature_id: str, company_type: str) -> tuple[str, str]:
    feature = feature_id.strip().upper()
    company = company_type.strip().upper()
    if not feature or not company:
        raise ValueError("feature_id and company_type must be non-empty")
    return feature, company


class ApplicabilityRegistry:
    """Stores explicit feature/company-type decisions.

    Absence is UNDECIDED by design. There is no implicit APPLIES default.
    """

    def __init__(self) -> None:
        self._decisions: dict[tuple[str, str], ApplicabilityDecision] = {}

    def set_decision(
        self,
        feature_id: str,
        company_type: str,
        decision: ApplicabilityDecision,
    ) -> None:
        self._decisions[_key(feature_id, company_type)] = decision

    def decision_for(
        self,
        feature_id: str,
        company_type: str,
    ) -> ApplicabilityDecision:
        return self._decisions.get(
            _key(feature_id, company_type),
            ApplicabilityDecision.UNDECIDED,
        )

    def require_applicable(
        self,
        feature_id: str,
        company_type: str,
    ) -> None:
        decision = self.decision_for(feature_id, company_type)
        if decision is not ApplicabilityDecision.APPLIES:
            raise FeatureApplicabilityError(
                f"{feature_id}/{company_type}: {decision.value}"
            )
