"""Source ingestion contracts for the free-first PIT pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .pit import require_aware_timestamp


def canonical_payload_sha256(payload: dict[str, Any]) -> str:
    """Return a deterministic SHA-256 for one JSON-compatible raw payload."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RawRecord:
    source: str
    source_record_key: str
    source_url: str
    retrieved_at: datetime
    payload: dict[str, Any]
    content_sha256: str
    source_published_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source is required")
        if not self.source_record_key.strip():
            raise ValueError("source_record_key is required")
        if not self.source_url.strip():
            raise ValueError("source_url is required")
        require_aware_timestamp(self.retrieved_at)
        if self.source_published_at is not None:
            require_aware_timestamp(self.source_published_at)
            if self.source_published_at > self.retrieved_at:
                raise ValueError("source_published_at cannot be after retrieved_at")

        expected_hash = canonical_payload_sha256(self.payload)
        if self.content_sha256 != expected_hash:
            raise ValueError("content_sha256 does not match payload")

    @classmethod
    def from_payload(
        cls,
        *,
        source: str,
        source_record_key: str,
        source_url: str,
        retrieved_at: datetime,
        payload: dict[str, Any],
        source_published_at: datetime | None = None,
    ) -> RawRecord:
        """Construct an immutable raw record and calculate its content hash."""
        return cls(
            source=source,
            source_record_key=source_record_key,
            source_url=source_url,
            retrieved_at=retrieved_at,
            payload=payload,
            content_sha256=canonical_payload_sha256(payload),
            source_published_at=source_published_at,
        )


@dataclass(frozen=True)
class PitRecord:
    source: str
    source_record_key: str
    source_url: str
    raw_content_sha256: str
    raw_retrieved_at: datetime
    reported_at: datetime | None
    available_at: datetime
    payload: dict[str, Any]
    quality_flag: str = "VERIFIED"

    def __post_init__(self) -> None:
        require_aware_timestamp(self.raw_retrieved_at)
        require_aware_timestamp(self.available_at)
        if self.reported_at is not None:
            require_aware_timestamp(self.reported_at)
            if self.available_at < self.reported_at:
                raise ValueError("available_at cannot precede reported_at")


def to_pit_record(
    raw: RawRecord,
    *,
    reported_at: datetime | None,
    available_at: datetime,
    quality_flag: str = "VERIFIED",
) -> PitRecord:
    """Convert one immutable raw observation to an explicit PIT record.

    No timestamp is inferred here. Callers must provide availability semantics
    derived from source evidence.
    """
    return PitRecord(
        source=raw.source,
        source_record_key=raw.source_record_key,
        source_url=raw.source_url,
        raw_content_sha256=raw.content_sha256,
        raw_retrieved_at=raw.retrieved_at,
        reported_at=reported_at,
        available_at=available_at,
        payload=raw.payload,
        quality_flag=quality_flag,
    )
