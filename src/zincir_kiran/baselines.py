"""Reproducible baseline contracts for Zincir Kıran research."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import IntEnum, StrEnum
from fractions import Fraction

from .pit import require_aware_timestamp


class Horizon(IntEnum):
    H20 = 20
    H60 = 60
    H120 = 120
    H252 = 252


class BaselineId(StrEnum):
    MARKET_BENCHMARK = "MARKET_BENCHMARK"
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    SIMPLE_VALUE = "SIMPLE_VALUE"
    SIMPLE_MOMENTUM = "SIMPLE_MOMENTUM"
    QVM = "QVM"
    TURKISH_FACTOR = "TURKISH_FACTOR"
    TOTAL_RASYO = "TOTAL_RASYO"


class BaselineRole(StrEnum):
    COMPARATOR = "COMPARATOR"
    FAILED_REFERENCE = "FAILED_REFERENCE"


REQUIRED_BASELINES = tuple(BaselineId)


def baseline_role(baseline_id: BaselineId) -> BaselineRole:
    """Keep Total Rasyo explicitly marked as a failed reference baseline."""
    if baseline_id is BaselineId.TOTAL_RASYO:
        return BaselineRole.FAILED_REFERENCE
    return BaselineRole.COMPARATOR


@dataclass(frozen=True)
class BaselineDefinition:
    baseline_id: BaselineId
    definition_version: str
    formula: str
    parameters: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.definition_version.strip():
            raise ValueError("definition_version is required")
        if not self.formula.strip():
            raise ValueError("formula is required")
        if tuple(sorted(self.parameters)) != self.parameters:
            raise ValueError("parameters must be sorted for deterministic definitions")


@dataclass
class BaselineRegistry:
    _definitions: dict[tuple[BaselineId, str], BaselineDefinition] = field(default_factory=dict)

    def register(self, definition: BaselineDefinition) -> None:
        """Register one version and reject contradictory rewrites."""
        key = (definition.baseline_id, definition.definition_version)
        existing = self._definitions.get(key)
        if existing is not None and existing != definition:
            raise ValueError("conflicting baseline definition version")
        self._definitions[key] = definition

    def get(self, baseline_id: BaselineId, definition_version: str) -> BaselineDefinition:
        key = (baseline_id, definition_version)
        try:
            return self._definitions[key]
        except KeyError as exc:
            raise KeyError("baseline definition is not registered") from exc


@dataclass(frozen=True)
class BaselineRunSpec:
    baseline_id: BaselineId
    definition_version: str
    horizon: Horizon
    data_snapshot_id: str
    universe_rule_version: str
    rebalance_specification: str
    created_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("definition_version", self.definition_version),
            ("data_snapshot_id", self.data_snapshot_id),
            ("universe_rule_version", self.universe_rule_version),
            ("rebalance_specification", self.rebalance_specification),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.created_at)


def equal_weight(security_ids: list[str]) -> tuple[tuple[str, Fraction], ...]:
    """Build deterministic equal weights without silently collapsing duplicates."""
    if not security_ids:
        raise ValueError("equal-weight baseline requires at least one security")
    if any(not security_id.strip() for security_id in security_ids):
        raise ValueError("security_id cannot be blank")
    if len(set(security_ids)) != len(security_ids):
        raise ValueError("duplicate security_id in equal-weight universe")

    ordered = sorted(security_ids)
    weight = Fraction(1, len(ordered))
    return tuple((security_id, weight) for security_id in ordered)


def market_relative_return(
    stock_total_return: Decimal | None,
    market_total_return: Decimal | None,
) -> Decimal:
    """Calculate the locked cross-sectional target without missing-value fill."""
    if stock_total_return is None or market_total_return is None:
        raise ValueError("missing return cannot be neutralized")
    return stock_total_return - market_total_return
