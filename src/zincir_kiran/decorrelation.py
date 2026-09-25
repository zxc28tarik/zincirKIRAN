"""Pairwise factor-correlation primitives for de-correlation research."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from statistics import fmean

from .factor_lab import average_ranks


class CorrelationMethod(StrEnum):
    PEARSON = "PEARSON"
    SPEARMAN = "SPEARMAN"


@dataclass(frozen=True)
class FactorPoint:
    observation_key: str
    value: float | None


@dataclass(frozen=True)
class PairwiseCorrelationResult:
    method: CorrelationMethod
    correlation: float | None
    overlap_count: int
    left_count: int
    right_count: int
    minimum_overlap: int

    @property
    def has_sufficient_overlap(self) -> bool:
        return self.overlap_count >= self.minimum_overlap


def _finite(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _as_unique_map(points: list[FactorPoint], *, side: str) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for point in points:
        key = point.observation_key.strip()
        if not key:
            raise ValueError(f"{side} observation_key cannot be blank")
        if key in result:
            raise ValueError(f"duplicate {side} observation_key: {key}")
        result[key] = point.value
    return result


def _pearson(left: tuple[float, ...], right: tuple[float, ...]) -> float | None:
    if len(left) != len(right):
        raise ValueError("correlation vectors must have equal length")
    if len(left) < 2:
        return None

    left_mean = fmean(left)
    right_mean = fmean(right)
    left_centered = tuple(value - left_mean for value in left)
    right_centered = tuple(value - right_mean for value in right)
    denominator = math.sqrt(
        sum(value * value for value in left_centered)
        * sum(value * value for value in right_centered)
    )
    if denominator == 0:
        return None

    numerator = sum(
        a * b for a, b in zip(left_centered, right_centered, strict=True)
    )
    return numerator / denominator


def pairwise_factor_correlation(
    left: list[FactorPoint],
    right: list[FactorPoint],
    *,
    minimum_overlap: int,
    method: CorrelationMethod,
) -> PairwiseCorrelationResult:
    """Align two factor series by common key and calculate explicit correlation.

    Missing and non-finite observations are excluded. If usable overlap is below
    ``minimum_overlap``, correlation is UNKNOWN (``None``), never zero.
    """
    if minimum_overlap < 2:
        raise ValueError("minimum_overlap must be at least 2")

    left_map = _as_unique_map(left, side="left")
    right_map = _as_unique_map(right, side="right")

    common_keys = sorted(set(left_map) & set(right_map))
    aligned = [
        (float(left_map[key]), float(right_map[key]))
        for key in common_keys
        if _finite(left_map[key]) and _finite(right_map[key])
    ]

    overlap_count = len(aligned)
    correlation: float | None = None
    if overlap_count >= minimum_overlap:
        left_values = tuple(pair[0] for pair in aligned)
        right_values = tuple(pair[1] for pair in aligned)
        if method is CorrelationMethod.PEARSON:
            correlation = _pearson(left_values, right_values)
        elif method is CorrelationMethod.SPEARMAN:
            correlation = _pearson(
                average_ranks(left_values),
                average_ranks(right_values),
            )
        else:
            raise ValueError(f"unsupported correlation method: {method}")

    return PairwiseCorrelationResult(
        method=method,
        correlation=correlation,
        overlap_count=overlap_count,
        left_count=len(left),
        right_count=len(right),
        minimum_overlap=minimum_overlap,
    )
