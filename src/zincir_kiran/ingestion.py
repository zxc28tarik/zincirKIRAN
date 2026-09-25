"""Source ingestion contracts for the free-first PIT pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawRecord:
    source: str
    source_url: str
    observed_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True)
class PitRecord:
    source: str
    source_url: str
    reported_at: datetime | None
    available_at: datetime
    payload: dict[str, Any]
    quality_flag: str = "VERIFIED"


def to_pit_record(
    raw: RawRecord,
    *,
    reported_at: datetime | None,
    available_at: datetime,
    quality_flag: str = "VERIFIED",
) -> PitRecord:
    """Convert a raw observation to an explicit PIT record.

    No timestamp is inferred here. Callers must provide availability semantics
    derived from source evidence.
    """
    return PitRecord(
        source=raw.source,
        source_url=raw.source_url,
        reported_at=reported_at,
        available_at=available_at,
        payload=raw.payload,
        quality_flag=quality_flag,
    )
