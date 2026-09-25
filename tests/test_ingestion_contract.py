from datetime import UTC, datetime

import pytest

from zincir_kiran.ingestion import (
    RawRecord,
    canonical_payload_sha256,
    to_pit_record,
)


def make_raw() -> RawRecord:
    return RawRecord.from_payload(
        source="KAP",
        source_record_key="KAP:TEST:1",
        source_url="https://kap.org.tr/example",
        retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
        source_published_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"ticker": "TEST", "value": 1},
    )


def test_canonical_hash_is_key_order_independent() -> None:
    left = {"ticker": "TEST", "nested": {"b": 2, "a": 1}}
    right = {"nested": {"a": 1, "b": 2}, "ticker": "TEST"}

    assert canonical_payload_sha256(left) == canonical_payload_sha256(right)


def test_raw_record_rejects_tampered_hash() -> None:
    with pytest.raises(ValueError, match="does not match payload"):
        RawRecord(
            source="KAP",
            source_record_key="KAP:TEST:1",
            source_url="https://kap.org.tr/example",
            retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
            payload={"ticker": "TEST"},
            content_sha256="0" * 64,
        )


def test_raw_record_rejects_future_publication_timestamp() -> None:
    with pytest.raises(ValueError, match="after retrieved_at"):
        RawRecord.from_payload(
            source="KAP",
            source_record_key="KAP:TEST:1",
            source_url="https://kap.org.tr/example",
            retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
            source_published_at=datetime(2026, 1, 2, tzinfo=UTC),
            payload={"ticker": "TEST"},
        )


def test_to_pit_record_requires_explicit_available_at() -> None:
    raw = make_raw()

    with pytest.raises(TypeError):
        to_pit_record(raw, reported_at=None)  # type: ignore[call-arg]


def test_to_pit_record_preserves_raw_provenance() -> None:
    raw = make_raw()
    available_at = datetime(2026, 1, 2, tzinfo=UTC)

    pit = to_pit_record(
        raw,
        reported_at=datetime(2026, 1, 1, tzinfo=UTC),
        available_at=available_at,
    )

    assert pit.source == "KAP"
    assert pit.source_record_key == "KAP:TEST:1"
    assert pit.source_url == raw.source_url
    assert pit.raw_content_sha256 == raw.content_sha256
    assert pit.raw_retrieved_at == raw.retrieved_at
    assert pit.available_at == available_at
    assert pit.payload == {"ticker": "TEST", "value": 1}
