"""Explicit feature applicability decisions by company type."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Applicability(StrEnum):
    APPLIES = "APPLIES"
    DOES_NOT_APPLY = "DOES_NOT_APPLY"
    UNDECIDED = "UNDECIDED"


@dataclass
class FeatureApplicabilityRegistry:
    _decisions: dict[tuple[str, str], Applicability] = field(default_factory=dict)

    def register(
        self,
        *,
        feature_id: str,
        company_type: str,
        state: Applicability,
    ) -> None:
        """Register one explicit decision and reject silent contradictory rewrites."""
        key = (feature_id.strip(), company_type.strip())
        if not key[0] or not key[1]:
            raise ValueError("feature_id and company_type are required")

        existing = self._decisions.get(key)
        if existing is not None and existing is not state:
            raise ValueError("conflicting applicability decision")
        self._decisions[key] = state

    def get(self, *, feature_id: str, company_type: str) -> Applicability:
        """Missing decisions are explicitly UNDECIDED, never neutral."""
        return self._decisions.get(
            (feature_id.strip(), company_type.strip()),
            Applicability.UNDECIDED,
        )

    def require_scoring_allowed(self, *, feature_id: str, company_type: str) -> None:
        """Permit factor scoring only for an explicit APPLIES decision."""
        state = self.get(feature_id=feature_id, company_type=company_type)
        if state is not Applicability.APPLIES:
            raise ValueError(f"feature scoring blocked: {state.value}")
