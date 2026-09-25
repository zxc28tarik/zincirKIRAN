"""Versioned candidate-factor library.

Factor definitions describe hypotheses. They are not evidence of production alpha.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EconomicFamily(StrEnum):
    VALUE = "VALUE"
    PROFITABILITY = "PROFITABILITY"
    QUALITY = "QUALITY"
    INVESTMENT_DISCIPLINE = "INVESTMENT_DISCIPLINE"
    FUNDAMENTAL_ACCELERATION = "FUNDAMENTAL_ACCELERATION"
    PRICE_MOMENTUM = "PRICE_MOMENTUM"
    EARNINGS_MOMENTUM = "EARNINGS_MOMENTUM"
    RISK = "RISK"
    LIQUIDITY = "LIQUIDITY"
    SIZE_CONTROL = "SIZE_CONTROL"


class ExpectedDirection(StrEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    CONTEXTUAL = "CONTEXTUAL"
    UNDECIDED = "UNDECIDED"


class FactorStage(StrEnum):
    CANDIDATE = "CANDIDATE"
    LAB_VALIDATED = "LAB_VALIDATED"
    PRODUCTION = "PRODUCTION"
    REJECTED = "REJECTED"


class EvidenceStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    SOURCED = "SOURCED"


@dataclass(frozen=True)
class FactorDefinition:
    factor_id: str
    definition_version: str
    economic_family: EconomicFamily
    economic_concept_key: str
    specification: str
    required_fields: tuple[str, ...]
    expected_direction: ExpectedDirection = ExpectedDirection.UNDECIDED
    stage: FactorStage = FactorStage.CANDIDATE
    evidence_status: EvidenceStatus = EvidenceStatus.UNREVIEWED
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("factor_id", self.factor_id),
            ("definition_version", self.definition_version),
            ("economic_concept_key", self.economic_concept_key),
            ("specification", self.specification),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")

        if not self.required_fields:
            raise ValueError("required_fields cannot be empty")
        normalized_fields = tuple(sorted(set(self.required_fields)))
        if normalized_fields != self.required_fields:
            raise ValueError("required_fields must be unique and sorted")
        if tuple(sorted(set(self.evidence_refs))) != self.evidence_refs:
            raise ValueError("evidence_refs must be unique and sorted")
        if self.evidence_status is EvidenceStatus.UNREVIEWED and self.evidence_refs:
            raise ValueError("unreviewed factor cannot claim evidence_refs")


@dataclass
class CandidateFactorRegistry:
    _definitions: dict[tuple[str, str], FactorDefinition] = field(default_factory=dict)

    def register(self, definition: FactorDefinition) -> None:
        """Register only candidate hypotheses; validation/promotion belongs to Factor Lab."""
        if definition.stage is not FactorStage.CANDIDATE:
            raise ValueError("candidate library accepts only CANDIDATE factors")

        key = (definition.factor_id, definition.definition_version)
        existing = self._definitions.get(key)
        if existing is not None and existing != definition:
            raise ValueError("conflicting factor definition version")
        self._definitions[key] = definition

    def get(self, factor_id: str, definition_version: str) -> FactorDefinition:
        try:
            return self._definitions[(factor_id, definition_version)]
        except KeyError as exc:
            raise KeyError("factor definition is not registered") from exc

    def definitions(self) -> tuple[FactorDefinition, ...]:
        return tuple(
            sorted(
                self._definitions.values(),
                key=lambda item: (item.economic_family.value, item.factor_id, item.definition_version),
            )
        )

    def concept_members(self, economic_concept_key: str) -> tuple[FactorDefinition, ...]:
        """Return alternative definitions sharing one economic idea."""
        return tuple(
            item
            for item in self.definitions()
            if item.economic_concept_key == economic_concept_key
        )


class MissingFactorInputError(ValueError):
    """Raised when a factor cannot be computed from the PIT snapshot."""


def require_factor_inputs(
    definition: FactorDefinition,
    observations: dict[str, Any],
) -> tuple[Any, ...]:
    """Return required values or reject missing/None inputs; never neutral-fill them."""
    missing = tuple(
        field_name
        for field_name in definition.required_fields
        if field_name not in observations or observations[field_name] is None
    )
    if missing:
        raise MissingFactorInputError(f"missing factor inputs: {missing}")
    return tuple(observations[field_name] for field_name in definition.required_fields)
