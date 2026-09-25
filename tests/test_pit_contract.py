from datetime import datetime, timezone

import pytest

from zincir_kiran.pit import available_by, latest_available_revision


UTC = timezone.utc


def ts(day: int) -> datetime:
    return datetime(2025, 1, day, 12, 0, tzinfo=UTC)


def test_future_information_is_not_available() -> None:
    record = {"available_at": ts(10)}
    assert available_by(record, ts(9)) is False
    assert available_by(record, ts(10)) is True


def test_later_revision_does_not_leak_into_earlier_snapshot() -> None:
    records = [
        {
            "company_id": "A",
            "metric_id": "revenue",
            "period_end": "2024-12-31",
            "revision_id": "r1",
            "value": 100,
            "available_at": ts(5),
        },
        {
            "company_id": "A",
            "metric_id": "revenue",
            "period_end": "2024-12-31",
            "revision_id": "r2",
            "value": 120,
            "available_at": ts(20),
        },
    ]

    identity = ("company_id", "metric_id", "period_end")

    early = latest_available_revision(records, ts(10), identity_fields=identity)
    late = latest_available_revision(records, ts(25), identity_fields=identity)

    assert early[0]["revision_id"] == "r1"
    assert early[0]["value"] == 100
    assert late[0]["revision_id"] == "r2"
    assert late[0]["value"] == 120


def test_missing_available_at_is_rejected_not_neutralized() -> None:
    records = [
        {
            "company_id": "A",
            "metric_id": "profit",
            "period_end": "2024-12-31",
            "revision_id": "r1",
            "value": None,
        }
    ]

    result = latest_available_revision(
        records,
        ts(25),
        identity_fields=("company_id", "metric_id", "period_end"),
    )

    assert result == []


def test_naive_prediction_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        available_by({"available_at": ts(5)}, datetime(2025, 1, 10, 12, 0))
