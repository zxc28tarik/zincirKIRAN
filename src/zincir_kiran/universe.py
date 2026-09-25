"""Historical investable-universe helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any


def investable_security_ids(
    rows: Iterable[Mapping[str, Any]],
    *,
    trade_date: date,
    model_rule_version: str,
) -> tuple[str, ...]:
    """Return the historical investable set for one date/rule version.

    Current listing status is intentionally irrelevant to this lookup.
    A security delisted today can remain in an older historical universe.
    """
    ids = {
        str(row["security_id"])
        for row in rows
        if row.get("trade_date") == trade_date
        and row.get("model_rule_version") == model_rule_version
        and row.get("is_investable") is True
    }
    return tuple(sorted(ids))
