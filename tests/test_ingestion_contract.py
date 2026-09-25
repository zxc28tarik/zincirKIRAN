from datetime import UTC, datetime

import pytest

from zincir_kiran.ingestion import RawRecord, to_pit_record


def test_to_pit_record_requires_explicit_available_at() -> None:
    raw = RawRecord(
        source="KAP",
        source_url="https://kap.org.tr/example",
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"ticker": "TEST"},
    )

    with pytest.raises(TypeError):
        to_pit_record(raw, reported_at=None)  # type: ignore[call-arg]


def test_to_pit_record_preserves_provenance() -> None:
    raw = RawRecord(
        source="KAP",
        source_url="https://kap.org.tr/example",
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"ticker": "TEST"},
    )
    available_at = datetime(2026, 1, 2, tzinfo=UTC)

    pit = to_pit_record(raw, reported_at=None, available_at=available_at)

    assert pit.source == "KAP"
    assert pit.source_url == raw.source_url
    assert pit.available_at == available_at
    assert pit.payload == {"ticker": "TEST"}
