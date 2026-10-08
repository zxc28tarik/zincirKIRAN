"""52W factor input-sufficiency and corporate-action risk gate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class High52InputStatus(StrEnum):
    READY = "READY"
    PRICE_HISTORY_INSUFFICIENT = "PRICE_HISTORY_INSUFFICIENT"
    CA_COVERAGE_INCOMPLETE = "CA_COVERAGE_INCOMPLETE"
    RECENT_CA_RISK_UNRESOLVED = "RECENT_CA_RISK_UNRESOLVED"
    HISTORICAL_CA_RECONCILIATION_REQUIRED = "HISTORICAL_CA_RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class High52InputEvidence:
    ticker: str
    adj_close_observations: int
    finite_positive_adj_close_observations: int
    recent_ca_coverage_complete: bool
    unresolved_recent_ca_event_ids: tuple[str, ...]
    historical_ca_lookback_reconciled: bool

    def __post_init__(self) -> None:
        if not self.ticker.strip():
            raise ValueError("ticker is required")
        if self.adj_close_observations < 0:
            raise ValueError("adj_close_observations cannot be negative")
        if self.finite_positive_adj_close_observations < 0:
            raise ValueError(
                "finite_positive_adj_close_observations cannot be negative"
            )
        if (
            self.finite_positive_adj_close_observations
            > self.adj_close_observations
        ):
            raise ValueError("finite-positive observations cannot exceed total")
        if self.unresolved_recent_ca_event_ids != tuple(
            sorted(set(self.unresolved_recent_ca_event_ids))
        ):
            raise ValueError(
                "unresolved_recent_ca_event_ids must be unique and sorted"
            )


@dataclass(frozen=True)
class High52InputGateResult:
    ticker: str
    status: High52InputStatus
    reason_codes: tuple[str, ...]
    score_computation_allowed: bool
    shadow_signal_allowed: bool


def evaluate_high52_input(
    evidence: High52InputEvidence,
) -> High52InputGateResult:
    reasons: list[str] = []

    if (
        evidence.adj_close_observations < 252
        or evidence.finite_positive_adj_close_observations < 252
    ):
        reasons.append("ADJ_CLOSE_252_REQUIRED")
        status = High52InputStatus.PRICE_HISTORY_INSUFFICIENT
    elif not evidence.recent_ca_coverage_complete:
        reasons.append("RECENT_CA_COVERAGE_INCOMPLETE")
        status = High52InputStatus.CA_COVERAGE_INCOMPLETE
    elif evidence.unresolved_recent_ca_event_ids:
        reasons.extend(
            f"UNRESOLVED_RECENT_CA:{event_id}"
            for event_id in evidence.unresolved_recent_ca_event_ids
        )
        status = High52InputStatus.RECENT_CA_RISK_UNRESOLVED
    elif not evidence.historical_ca_lookback_reconciled:
        reasons.append("HISTORICAL_252D_CA_RECONCILIATION_REQUIRED")
        status = High52InputStatus.HISTORICAL_CA_RECONCILIATION_REQUIRED
    else:
        status = High52InputStatus.READY

    score_allowed = status is High52InputStatus.READY
    return High52InputGateResult(
        ticker=evidence.ticker,
        status=status,
        reason_codes=tuple(sorted(reasons)),
        score_computation_allowed=score_allowed,
        # 45D is evidence preparation only. Even READY input evidence cannot
        # emit a real shadow signal in this implementation.
        shadow_signal_allowed=False,
    )
