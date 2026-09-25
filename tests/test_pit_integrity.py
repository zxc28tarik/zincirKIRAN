from datetime import date, datetime

import pytest

from zincir_kiran.availability import ISTANBUL, next_trading_day_available_at
from zincir_kiran.identity import identifier_at
from zincir_kiran.pit import available_by, latest_available_revision
from zincir_kiran.quality import finite_or_none
from zincir_kiran.universe import investable_security_ids


def test_ticker_change_keeps_stable_security_identity() -> None:
    rows = [
        {
            "security_id": "S1",
            "ticker": "OLD",
            "valid_from": date(2020, 1, 1),
            "valid_to": date(2024, 12, 31),
        },
        {
            "security_id": "S1",
            "ticker": "NEW",
            "valid_from": date(2025, 1, 1),
            "valid_to": None,
        },
    ]

    old = identifier_at(rows, security_id="S1", as_of=date(2024, 6, 1))
    new = identifier_at(rows, security_id="S1", as_of=date(2025, 6, 1))

    assert old is not None and old["ticker"] == "OLD"
    assert new is not None and new["ticker"] == "NEW"
    assert old["security_id"] == new["security_id"] == "S1"


def test_overlapping_ticker_history_is_rejected_instead_of_guessed() -> None:
    rows = [
        {
            "security_id": "S1",
            "ticker": "AAA",
            "valid_from": date(2025, 1, 1),
            "valid_to": None,
        },
        {
            "security_id": "S1",
            "ticker": "BBB",
            "valid_from": date(2025, 2, 1),
            "valid_to": None,
        },
    ]

    with pytest.raises(ValueError, match="ambiguous"):
        identifier_at(rows, security_id="S1", as_of=date(2025, 3, 1))


def test_delisted_today_security_remains_in_historical_universe() -> None:
    rows = [
        {
            "trade_date": date(2020, 1, 2),
            "security_id": "DELISTED_NOW",
            "is_investable": True,
            "model_rule_version": "v1",
            "current_listing_status": "DELISTED",
        },
        {
            "trade_date": date(2020, 1, 2),
            "security_id": "OTHER",
            "is_investable": False,
            "model_rule_version": "v1",
        },
    ]

    result = investable_security_ids(
        rows,
        trade_date=date(2020, 1, 2),
        model_rule_version="v1",
    )

    assert result == ("DELISTED_NOW",)


def test_date_only_publication_moves_to_next_trading_day() -> None:
    available_at = next_trading_day_available_at(
        date(2025, 1, 3),
        [date(2025, 1, 3), date(2025, 1, 6), date(2025, 1, 7)],
    )

    assert available_at == datetime(2025, 1, 6, 0, 0, tzinfo=ISTANBUL)


def test_corporate_action_cannot_be_seen_before_its_available_at() -> None:
    action = {"available_at": datetime(2025, 4, 10, 18, 0, tzinfo=ISTANBUL)}

    assert available_by(
        action,
        datetime(2025, 4, 10, 17, 59, tzinfo=ISTANBUL),
    ) is False
    assert available_by(
        action,
        datetime(2025, 4, 10, 18, 0, tzinfo=ISTANBUL),
    ) is True


def test_missing_and_nonfinite_values_are_not_neutralized() -> None:
    assert finite_or_none(None) is None
    assert finite_or_none(float("nan")) is None
    assert finite_or_none(float("inf")) is None
    assert finite_or_none(True) is None
    assert finite_or_none(0.5) == 0.5


def test_snapshot_order_is_deterministic_for_same_timestamp() -> None:
    timestamp = datetime(2025, 3, 1, 18, 0, tzinfo=ISTANBUL)
    rows = [
        {
            "company_id": "B",
            "metric_id": "revenue",
            "period_end": "2024-12-31",
            "revision_id": "r1",
            "available_at": timestamp,
        },
        {
            "company_id": "A",
            "metric_id": "revenue",
            "period_end": "2024-12-31",
            "revision_id": "r1",
            "available_at": timestamp,
        },
    ]
    identity = ("company_id", "metric_id", "period_end")

    forward = latest_available_revision(
        rows,
        timestamp,
        identity_fields=identity,
    )
    reverse = latest_available_revision(
        reversed(rows),
        timestamp,
        identity_fields=identity,
    )

    assert [row["company_id"] for row in forward] == ["A", "B"]
    assert forward == reverse
