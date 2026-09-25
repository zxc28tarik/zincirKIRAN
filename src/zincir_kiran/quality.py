"""Feature-value quality helpers."""

from __future__ import annotations

import math
from numbers import Real


def finite_or_none(value: object) -> float | None:
    """Return a finite numeric value or None; never manufacture a neutral score."""
    if not isinstance(value, Real) or isinstance(value, bool):
        return None
    result = float(value)
    if not math.isfinite(result):
        return None
    return result
