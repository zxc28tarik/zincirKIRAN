"""Historical security identity helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any


def identifier_at(
    rows: Iterable[Mapping[str, Any]],
    *,
    security_id: str,
    as_of: date,
) -> Mapping[str, Any] | None:
    """Resolve one security identifier valid on a historical date.

    Company/security identity stays stable while ticker labels may change.
    Ambiguous overlapping identifiers are rejected instead of guessed.
    """
    matches: list[Mapping[str, Any]] = []
    for row in rows:
        if str(row.get("security_id")) != security_id:
            continue
        valid_from = row.get("valid_from")
        valid_to = row.get("valid_to")
        if not isinstance(valid_from, date):
            continue
        if valid_from > as_of:
            continue
        if isinstance(valid_to, date) and valid_to < as_of:
            continue
        matches.append(row)

    if len(matches) > 1:
        raise ValueError("ambiguous overlapping security identifiers")
    return matches[0] if matches else None
