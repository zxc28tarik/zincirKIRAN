"""Availability-time rules for incomplete source timestamps."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")


def next_trading_day_available_at(
    publication_date: date,
    trading_dates: Iterable[date],
) -> datetime:
    """Apply a conservative fallback when a source has date but no exact time.

    The information becomes usable at 00:00 Europe/Istanbul on the first
    known trading date strictly after publication_date. This prevents
    accidental same-day look-ahead.
    """
    candidates = sorted(day for day in set(trading_dates) if day > publication_date)
    if not candidates:
        raise ValueError("no later trading date available")
    return datetime.combine(candidates[0], time.min, tzinfo=ISTANBUL)
