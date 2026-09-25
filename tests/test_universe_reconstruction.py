from datetime import date

import pytest

from zincir_kiran.universe_reconstruction import (
    ListingInterval,
    listed_security_ids,
    validate_non_overlapping_intervals,
)


def test_delisted_security_remains_in_pre_delisting_universe() -> None:
    intervals = [
        ListingInterval(
            security_id="OLDCO",
            first_trade_date=date(2018, 1, 2),
            last_trade_date=date(2022, 6, 30),
        ),
        ListingInterval(
            security_id="LIVE",
            first_trade_date=date(2019, 1, 2),
        ),
    ]

    assert listed_security_ids(intervals, trade_date=date(2020, 1, 2)) == ("LIVE", "OLDCO")
    assert listed_security_ids(intervals, trade_date=date(2023, 1, 2)) == ("LIVE",)


def test_current_status_is_not_needed_to_reconstruct_history() -> None:
    interval = ListingInterval(
        security_id="DELISTED_TODAY",
        first_trade_date=date(2010, 1, 4),
        last_trade_date=date(2024, 12, 31),
    )
    assert listed_security_ids([interval], trade_date=date(2015, 5, 5)) == ("DELISTED_TODAY",)


def test_overlapping_listing_intervals_are_rejected() -> None:
    intervals = [
        ListingInterval("S1", date(2020, 1, 1), date(2021, 12, 31)),
        ListingInterval("S1", date(2021, 12, 31), date(2022, 12, 31)),
    ]
    with pytest.raises(ValueError, match="overlapping"):
        validate_non_overlapping_intervals(intervals)
