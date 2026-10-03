"""Versioned immutable aggregation specifications for Interpretable Alpha v1."""

from __future__ import annotations

from dataclasses import dataclass, field

from .baselines import Horizon


@dataclass(frozen=True)
class AlphaAggregationSpec:
    specification_id: str
    definition_version: str
    horizon: Horizon
    aggregation_rule_id: str
    normalization_rule_id: str
    weight_policy_id: str
    coverage_rule_id: str
    parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("specification_id", self.specification_id),
            ("definition_version", self.definition_version),
            ("aggregation_rule_id", self.aggregation_rule_id),
            ("normalization_rule_id", self.normalization_rule_id),
            ("weight_policy_id", self.weight_policy_id),
            ("coverage_rule_id", self.coverage_rule_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")

        normalized_parameters = tuple(sorted(set(self.parameters)))
        if normalized_parameters != self.parameters:
            raise ValueError("parameters must be unique and sorted")


@dataclass
class AlphaAggregationRegistry:
    _specifications: dict[tuple[str, str], AlphaAggregationSpec] = field(
        default_factory=dict
    )

    def register(self, specification: AlphaAggregationSpec) -> None:
        """Register one immutable aggregation specification version."""
        key = (specification.specification_id, specification.definition_version)
        existing = self._specifications.get(key)
        if existing is not None and existing != specification:
            raise ValueError("conflicting alpha aggregation specification version")
        self._specifications[key] = specification

    def get(self, specification_id: str, definition_version: str) -> AlphaAggregationSpec:
        try:
            return self._specifications[(specification_id, definition_version)]
        except KeyError as exc:
            raise KeyError("alpha aggregation specification is not registered") from exc
