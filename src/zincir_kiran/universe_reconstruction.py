"""Historical universe reconstruction from stable security listing intervals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ListingInterval:
    security_id: str
    first_trade_date: date
    last_trade_date: date | None = None

    def __post_init__(self) -> None:
        if self.last_trade_date is not None and self.last_trade_date < self.first_trade_date:
            raise ValueError("last_trade_date cannot precede first_trade_date")

    def contains(self, trade_date: date) -> bool:
        if trade_date < self.first_trade_date:
            return False
        if self.last_trade_date is not None and trade_date > self.last_trade_date:
            return False
        return True


def listed_security_ids(
    intervals: list[ListingInterval],
    *,
    trade_date: date,
) -> tuple[str, ...]:
    """Return securities actually listed on a historical trading date."""
    result = {interval.security_id for interval in intervals if interval.contains(trade_date)}
    return tuple(sorted(result))


def validate_non_overlapping_intervals(intervals: list[ListingInterval]) -> None:
    """Reject overlapping listing intervals for the same stable security identity."""
    grouped: dict[str, list[ListingInterval]] = {}
    for interval in intervals:
        grouped.setdefault(interval.security_id, []).append(interval)

    for security_id, rows in grouped.items():
        rows.sort(key=lambda item: item.first_trade_date)
        for previous, current in zip(rows, rows[1:], strict=False):
            if previous.last_trade_date is None:
                raise ValueError(f"open-ended interval overlaps for {security_id}")
            if current.first_trade_date <= previous.last_trade_date:
                raise ValueError(f"overlapping listing intervals for {security_id}")
