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

class RedundancyEdgeState(StrEnum):
    REDUNDANCY_CANDIDATE = "REDUNDANCY_CANDIDATE"
    BELOW_THRESHOLD = "BELOW_THRESHOLD"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RedundancyEdgeDecision:
    state: RedundancyEdgeState
    absolute_threshold: float
    correlation: float | None
    overlap_count: int

    @property
    def has_edge(self) -> bool | None:
        """Return True/False only when statistical evidence is available."""
        if self.state is RedundancyEdgeState.UNKNOWN:
            return None
        return self.state is RedundancyEdgeState.REDUNDANCY_CANDIDATE


def redundancy_edge_decision(
    result: PairwiseCorrelationResult,
    *,
    absolute_threshold: float,
) -> RedundancyEdgeDecision:
    """Classify one pair using an explicit caller-supplied absolute threshold.

    This is a redundancy-candidate edge, not a causal claim and not a factor
    deletion/promotion decision. Unknown correlation remains UNKNOWN.
    """
    if not 0 < absolute_threshold <= 1:
        raise ValueError("absolute_threshold must be in (0, 1]")

    if result.correlation is None:
        state = RedundancyEdgeState.UNKNOWN
    elif abs(result.correlation) >= absolute_threshold:
        state = RedundancyEdgeState.REDUNDANCY_CANDIDATE
    else:
        state = RedundancyEdgeState.BELOW_THRESHOLD

    return RedundancyEdgeDecision(
        state=state,
        absolute_threshold=absolute_threshold,
        correlation=result.correlation,
        overlap_count=result.overlap_count,
    )

@dataclass(frozen=True)
class FactorRedundancyEdge:
    left_factor_id: str
    right_factor_id: str
    decision: RedundancyEdgeDecision

    def __post_init__(self) -> None:
        if not self.left_factor_id.strip() or not self.right_factor_id.strip():
            raise ValueError("factor ids are required")
        if self.left_factor_id == self.right_factor_id:
            raise ValueError("redundancy edge cannot be a self-edge")

    @property
    def normalized_pair(self) -> tuple[str, str]:
        return tuple(sorted((self.left_factor_id, self.right_factor_id)))  # type: ignore[return-value]


@dataclass(frozen=True)
class RedundancyGraph:
    factor_ids: tuple[str, ...]
    candidate_edges: tuple[tuple[str, str], ...]
    components: tuple[tuple[str, ...], ...]


def build_redundancy_graph(
    factor_ids: list[str],
    edges: list[FactorRedundancyEdge],
) -> RedundancyGraph:
    """Build deterministic undirected redundancy components.

    Only REDUNDANCY_CANDIDATE edges connect factors. BELOW_THRESHOLD and
    UNKNOWN remain auditable evidence but do not create graph connectivity.
    No winner, deletion, or weight change is selected here.
    """
    cleaned = [factor_id.strip() for factor_id in factor_ids]
    if any(not factor_id for factor_id in cleaned):
        raise ValueError("factor_id cannot be blank")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("duplicate factor_id in graph universe")

    universe = set(cleaned)
    states_by_pair: dict[tuple[str, str], RedundancyEdgeState] = {}
    for edge in edges:
        left, right = edge.normalized_pair
        if left not in universe or right not in universe:
            raise ValueError("edge references factor outside graph universe")

        existing = states_by_pair.get((left, right))
        if existing is not None and existing is not edge.decision.state:
            raise ValueError("conflicting duplicate redundancy edge")
        states_by_pair[(left, right)] = edge.decision.state

    candidate_edges = tuple(
        sorted(
            pair
            for pair, state in states_by_pair.items()
            if state is RedundancyEdgeState.REDUNDANCY_CANDIDATE
        )
    )

    adjacency: dict[str, set[str]] = {factor_id: set() for factor_id in cleaned}
    for left, right in candidate_edges:
        adjacency[left].add(right)
        adjacency[right].add(left)

    components: list[tuple[str, ...]] = []
    visited: set[str] = set()
    for start in sorted(cleaned):
        if start in visited:
            continue

        stack = [start]
        members: list[str] = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            members.append(current)
            stack.extend(
                neighbor
                for neighbor in sorted(adjacency[current], reverse=True)
                if neighbor not in visited
            )

        components.append(tuple(sorted(members)))

    components.sort(key=lambda component: component)
    return RedundancyGraph(
        factor_ids=tuple(sorted(cleaned)),
        candidate_edges=candidate_edges,
        components=tuple(components),
    )
