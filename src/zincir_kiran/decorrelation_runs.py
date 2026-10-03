"""Immutable de-correlation run metadata contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .decorrelation import CorrelationMethod
from .pit import require_aware_timestamp


@dataclass(frozen=True)
class DecorrelationRunSpec:
    run_id: str
    data_snapshot_id: str
    universe_rule_version: str
    correlation_method: CorrelationMethod
    minimum_overlap: int
    absolute_threshold: float
    residualization_include_intercept: bool
    preregistered_at: datetime

    def __post_init__(self) -> None:
        for name, value in (
            ("run_id", self.run_id),
            ("data_snapshot_id", self.data_snapshot_id),
            ("universe_rule_version", self.universe_rule_version),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.minimum_overlap < 2:
            raise ValueError("minimum_overlap must be at least 2")
        if not 0 < self.absolute_threshold <= 1:
            raise ValueError("absolute_threshold must be in (0, 1]")
        if not isinstance(self.residualization_include_intercept, bool):
            raise TypeError("residualization_include_intercept must be a bool")
        require_aware_timestamp(self.preregistered_at)


@dataclass
class DecorrelationRunRegistry:
    _runs: dict[str, DecorrelationRunSpec] = field(default_factory=dict)

    def register(self, spec: DecorrelationRunSpec) -> None:
        """Register one immutable run protocol before de-correlation results exist."""
        existing = self._runs.get(spec.run_id)
        if existing is not None and existing != spec:
            raise ValueError("conflicting de-correlation run pre-registration")
        self._runs[spec.run_id] = spec

    def get(self, run_id: str) -> DecorrelationRunSpec:
        try:
            return self._runs[run_id]
        except KeyError as exc:
            raise KeyError("de-correlation run is not pre-registered") from exc
