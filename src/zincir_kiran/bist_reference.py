"""Borsa Istanbul reference-data normalization.

The first-trading-date record layout follows Borsa Istanbul reporting formats.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Sequence


@dataclass(frozen=True)
class BistFirstTradingRecord:
    first_code: str
    current_code: str
    current_name: str
    listing_date: date
    first_trading_date: date
    first_trading_close_try: Decimal


def _parse_ddmmyyyy(value: str) -> date:
    return datetime.strptime(value.strip(), "%d.%m.%Y").date()


def parse_first_trading_fields(fields: Sequence[str]) -> BistFirstTradingRecord:
    """Parse the six official Borsa Istanbul first-trading-date fields."""
    if len(fields) != 6:
        raise ValueError("expected exactly 6 Borsa Istanbul first-trading fields")

    first_code, current_code, current_name, listing, first_trade, first_close = (
        value.strip() for value in fields
    )
    if not first_code or not current_code or not current_name:
        raise ValueError("security codes and company name are required")

    try:
        close = Decimal(first_close)
    except InvalidOperation as exc:
        raise ValueError("invalid first trading close") from exc

    return BistFirstTradingRecord(
        first_code=first_code,
        current_code=current_code,
        current_name=current_name,
        listing_date=_parse_ddmmyyyy(listing),
        first_trading_date=_parse_ddmmyyyy(first_trade),
        first_trading_close_try=close,
    )


def parse_first_trading_semicolon_line(line: str) -> BistFirstTradingRecord:
    """Parse the semicolon-delimited representation documented by Borsa Istanbul."""
    return parse_first_trading_fields(line.rstrip("\n").split(";"))
