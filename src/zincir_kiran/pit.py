"""Point-in-time selection primitives.

These functions are deliberately small and dependency-free so PIT semantics can be
unit-tested before any database or factor logic is trusted.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any


def require_aware_timestamp(value: datetime) -> None:
    """Reject naive timestamps because PIT comparisons must be timezone-aware."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("PIT timestamps must be timezone-aware")


def available_by(
    record: Mapping[str, Any],
    prediction_timestamp: datetime,
    *,
    field: str = "available_at",
) -> bool:
    """Return True only when a record was safely available by prediction time."""
    require_aware_timestamp(prediction_timestamp)
    available_at = record.get(field)
    if not isinstance(available_at, datetime):
        return False
    require_aware_timestamp(available_at)
    return available_at <= prediction_timestamp


def latest_available_revision(
    records: Iterable[Mapping[str, Any]],
    prediction_timestamp: datetime,
    *,
    identity_fields: tuple[str, ...],
) -> list[Mapping[str, Any]]:
    """Select the latest available revision for each logical fact identity."""
    require_aware_timestamp(prediction_timestamp)

    latest: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for record in records:
        if not available_by(record, prediction_timestamp):
            continue

        key = tuple(record.get(field) for field in identity_fields)
        existing = latest.get(key)

        if existing is None:
            latest[key] = record
            continue

        candidate_ts = record["available_at"]
        existing_ts = existing["available_at"]
        if candidate_ts > existing_ts:
            latest[key] = record
        elif candidate_ts == existing_ts:
            candidate_rev = str(record.get("revision_id", ""))
            existing_rev = str(existing.get("revision_id", ""))
            if candidate_rev > existing_rev:
                latest[key] = record

    def stable_key(
        item: tuple[tuple[Any, ...], Mapping[str, Any]],
    ) -> tuple[str, ...]:
        return tuple("" if part is None else str(part) for part in item[0])

    return [record for _, record in sorted(latest.items(), key=stable_key)]
