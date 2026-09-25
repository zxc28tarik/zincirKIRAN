"""Corporate-action normalization for point-in-time research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class CorporateActionType(StrEnum):
    CASH_DIVIDEND = "CASH_DIVIDEND"
    BONUS_ISSUE = "BONUS_ISSUE"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    SPLIT = "SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"
    MERGER = "MERGER"
    DEMERGER = "DEMERGER"
    TICKER_CHANGE = "TICKER_CHANGE"
    DELISTING = "DELISTING"


@dataclass(frozen=True)
class CorporateAction:
    security_id: str
    action_type: CorporateActionType
    available_at: datetime
    announcement_at: datetime | None = None
    ex_date: date | None = None
    record_date: date | None = None
    payment_date: date | None = None
    ratio: float | None = None
    cash_amount: float | None = None
    currency: str | None = None
    source_url: str | None = None

    def __post_init__(self) -> None:
        require_aware_timestamp(self.available_at)
        if self.announcement_at is not None:
            require_aware_timestamp(self.announcement_at)
            if self.available_at < self.announcement_at:
                raise ValueError("available_at cannot precede announcement_at")
        if self.ratio is not None and self.ratio < 0:
            raise ValueError("ratio cannot be negative")
        if self.cash_amount is not None and self.cash_amount < 0:
            raise ValueError("cash_amount cannot be negative")
        if (
            self.record_date is not None
            and self.ex_date is not None
            and self.record_date < self.ex_date
        ):
            raise ValueError("record_date cannot precede ex_date")
        if (
            self.payment_date is not None
            and self.ex_date is not None
            and self.payment_date < self.ex_date
        ):
            raise ValueError("payment_date cannot precede ex_date")


def visible_actions(
    actions: list[CorporateAction],
    prediction_timestamp: datetime,
) -> tuple[CorporateAction, ...]:
    """Return only actions knowable by the prediction timestamp."""
    require_aware_timestamp(prediction_timestamp)
    return tuple(
        sorted(
            (action for action in actions if action.available_at <= prediction_timestamp),
            key=lambda action: (action.available_at, action.security_id, action.action_type.value),
        )
    )
