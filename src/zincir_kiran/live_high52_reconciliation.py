"""Historical 252-day corporate-action reconciliation for live HIGH_52W."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class High52ReconciledStatus(StrEnum):
    PRICE_HISTORY_INSUFFICIENT = "PRICE_HISTORY_INSUFFICIENT"
    HISTORICAL_CA_COVERAGE_INCOMPLETE = "HISTORICAL_CA_COVERAGE_INCOMPLETE"
    HISTORICAL_CA_RISK_UNRESOLVED = "HISTORICAL_CA_RISK_UNRESOLVED"
    RECENT_CA_RISK_UNRESOLVED = "RECENT_CA_RISK_UNRESOLVED"
    FACTOR_INPUT_READY = "FACTOR_INPUT_READY"


@dataclass(frozen=True)
class High52ReconciliationEvidence:
    ticker: str
    finite_positive_adj_close_observations: int
    historical_ca_coverage_complete: bool
    unresolved_historical_ca_event_ids: tuple[str, ...]
    unresolved_recent_ca_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.ticker.strip():
            raise ValueError("ticker is required")
        if self.finite_positive_adj_close_observations < 0:
            raise ValueError(
                "finite_positive_adj_close_observations cannot be negative"
            )
        for name, values in (
            (
                "unresolved_historical_ca_event_ids",
                self.unresolved_historical_ca_event_ids,
            ),
            (
                "unresolved_recent_ca_event_ids",
                self.unresolved_recent_ca_event_ids,
            ),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"{name} must be unique and sorted")


@dataclass(frozen=True)
class High52ReconciliationResult:
    ticker: str
    status: High52ReconciledStatus
    reason_codes: tuple[str, ...]
    factor_input_ready: bool
    score_computation_allowed: bool
    shadow_signal_allowed: bool


def evaluate_high52_reconciliation(
    evidence: High52ReconciliationEvidence,
) -> High52ReconciliationResult:
    reasons: list[str] = []

    if evidence.finite_positive_adj_close_observations < 252:
        status = High52ReconciledStatus.PRICE_HISTORY_INSUFFICIENT
        reasons.append("ADJ_CLOSE_252_REQUIRED")
    elif not evidence.historical_ca_coverage_complete:
        status = High52ReconciledStatus.HISTORICAL_CA_COVERAGE_INCOMPLETE
        reasons.append("HISTORICAL_CA_COVERAGE_INCOMPLETE")
    elif evidence.unresolved_historical_ca_event_ids:
        status = High52ReconciledStatus.HISTORICAL_CA_RISK_UNRESOLVED
        reasons.extend(
            f"UNRESOLVED_HISTORICAL_CA:{event_id}"
            for event_id in evidence.unresolved_historical_ca_event_ids
        )
    elif evidence.unresolved_recent_ca_event_ids:
        status = High52ReconciledStatus.RECENT_CA_RISK_UNRESOLVED
        reasons.extend(
            f"UNRESOLVED_RECENT_CA:{event_id}"
            for event_id in evidence.unresolved_recent_ca_event_ids
        )
    else:
        status = High52ReconciledStatus.FACTOR_INPUT_READY

    ready = status is High52ReconciledStatus.FACTOR_INPUT_READY
    return High52ReconciliationResult(
        ticker=evidence.ticker,
        status=status,
        reason_codes=tuple(sorted(reasons)),
        factor_input_ready=ready,
        score_computation_allowed=ready,
        # 45E validates factor inputs only. A later prospective run contract
        # must separately authorize any actual shadow observation.
        shadow_signal_allowed=False,
    )
