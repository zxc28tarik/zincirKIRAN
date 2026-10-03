"""Interpretable Alpha v1 contracts and admitted-factor input gates."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum

from .baselines import Horizon


class AdmissionDecision(StrEnum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    UNDECIDED = "UNDECIDED"


ALPHA_FIELD_BY_HORIZON: dict[Horizon, str] = {
    Horizon.H20: "Alpha20",
    Horizon.H60: "Alpha60",
    Horizon.H120: "Alpha120",
    Horizon.H252: "Alpha252",
}


def alpha_field_name(horizon: Horizon) -> str:
    """Return the locked public alpha field for one research horizon."""
    try:
        return ALPHA_FIELD_BY_HORIZON[horizon]
    except KeyError as exc:
        raise ValueError("unsupported alpha horizon") from exc


@dataclass(frozen=True)
class FactorAdmission:
    admission_id: str
    factor_id: str
    factor_definition_version: str
    horizon: Horizon
    decision: AdmissionDecision
    factor_lab_experiment_id: str
    decorrelation_run_id: str
    decorrelation_component_id: str
    rationale: str

    def __post_init__(self) -> None:
        for name, value in (
            ("admission_id", self.admission_id),
            ("factor_id", self.factor_id),
            ("factor_definition_version", self.factor_definition_version),
            ("factor_lab_experiment_id", self.factor_lab_experiment_id),
            ("decorrelation_run_id", self.decorrelation_run_id),
            ("decorrelation_component_id", self.decorrelation_component_id),
            ("rationale", self.rationale),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        alpha_field_name(self.horizon)


@dataclass
class FactorAdmissionRegistry:
    _records: dict[str, FactorAdmission] = field(default_factory=dict)

    def register(self, admission: FactorAdmission) -> None:
        """Register an explicit admission decision without silently rewriting it."""
        existing = self._records.get(admission.admission_id)
        if existing is not None and existing != admission:
            raise ValueError("conflicting factor admission record")
        self._records[admission.admission_id] = admission

    def get(self, admission_id: str) -> FactorAdmission:
        try:
            return self._records[admission_id]
        except KeyError as exc:
            raise KeyError("factor admission is not registered") from exc


@dataclass(frozen=True)
class AdmittedFactorInput:
    admission: FactorAdmission
    signal_value: float | None


def require_admitted_factor_inputs(
    inputs: list[AdmittedFactorInput],
    *,
    horizon: Horizon,
) -> tuple[AdmittedFactorInput, ...]:
    """Gate Alpha v1 inputs without aggregation, neutral fill, or hidden promotion."""
    alpha_field_name(horizon)
    accepted: list[AdmittedFactorInput] = []
    seen: set[tuple[str, str]] = set()

    for item in inputs:
        admission = item.admission
        if admission.horizon is not horizon:
            raise ValueError("factor admission horizon does not match alpha horizon")
        if admission.decision is not AdmissionDecision.ADMITTED:
            raise ValueError(f"factor input is not admitted: {admission.decision.value}")
        if item.signal_value is None or not math.isfinite(item.signal_value):
            raise ValueError("admitted factor input must have a finite signal_value")

        key = (admission.factor_id, admission.factor_definition_version)
        if key in seen:
            raise ValueError("duplicate admitted factor definition")
        seen.add(key)
        accepted.append(item)

    return tuple(
        sorted(
            accepted,
            key=lambda item: (
                item.admission.factor_id,
                item.admission.factor_definition_version,
                item.admission.admission_id,
            ),
        )
    )
