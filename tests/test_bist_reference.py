from datetime import date
from decimal import Decimal

import pytest

from zincir_kiran.bist_reference import parse_first_trading_semicolon_line


def test_parse_official_first_trading_sample() -> None:
    record = parse_first_trading_semicolon_line(
        "AKFIN;GARFA;GARANTİ FAKTORİNG A.Ş. ;20.12.1993;21.12.1993;7700.00"
    )

    assert record.first_code == "AKFIN"
    assert record.current_code == "GARFA"
    assert record.current_name == "GARANTİ FAKTORİNG A.Ş."
    assert record.listing_date == date(1993, 12, 20)
    assert record.first_trading_date == date(1993, 12, 21)
    assert record.first_trading_close_try == Decimal("7700.00")


def test_first_trading_parser_rejects_wrong_column_count() -> None:
    with pytest.raises(ValueError, match="exactly 6"):
        parse_first_trading_semicolon_line("AAA;BBB")
