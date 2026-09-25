"""Availability-time rules for point-in-time research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from .pit import require_aware_timestamp


ISTANBUL = ZoneInfo("Europe/Istanbul")


@dataclass(frozen=True)
class AvailabilityDecision:
    available_at: datetime
    quality_flag: str
    rule: str


def next_trading_day_available_at(
    publication_date: date,
    trading_dates: Iterable[date],
) -> datetime:
    """Legacy conservative fallback for a date-only publication.

    This helper keeps the existing PIT contract: the value becomes usable on
    the first known trading date strictly after the publication date. New
    ingestion code should prefer ``from_date_only_publication`` when an
    explicit trading-session timestamp is available.
    """
    candidates = sorted(day for day in set(trading_dates) if day > publication_date)
    if not candidates:
        raise ValueError("no later trading date available")
    return datetime.combine(candidates[0], time.min, tzinfo=ISTANBUL)


def from_exact_publication_timestamp(published_at: datetime) -> AvailabilityDecision:
    """Use an exact source publication timestamp without alteration."""
    require_aware_timestamp(published_at)
    return AvailabilityDecision(
        available_at=published_at,
        quality_flag="VERIFIED",
        rule="EXACT_PUBLICATION_TIMESTAMP",
    )


def from_date_only_publication(
    publication_date: date,
    *,
    next_trading_session: datetime,
) -> AvailabilityDecision:
    """Defer date-only evidence to an explicitly supplied later trading session.

    The session timestamp must come from a trading calendar or another explicit
    source. This function deliberately does not invent an exchange open time.
    """
    require_aware_timestamp(next_trading_session)
    if next_trading_session.date() <= publication_date:
        raise ValueError("next_trading_session must be after publication_date")

    return AvailabilityDecision(
        available_at=next_trading_session,
        quality_flag="ESTIMATED_TIMESTAMP",
        rule="DATE_ONLY_DEFER_TO_NEXT_TRADING_SESSION",
    )
