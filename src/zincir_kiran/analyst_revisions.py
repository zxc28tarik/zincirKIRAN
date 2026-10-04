"""Analyst estimate/revision ingestion contracts for Zincir Kıran."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class EstimateAuthority(StrEnum):
    HISTORICAL_PIT = "HISTORICAL_PIT"
    CURRENT_ONLY = "CURRENT_ONLY"


@dataclass(frozen=True)
class AnalystEstimateSnapshot:
    ticker: str
    fiscal_period_end: datetime
    estimate_at: datetime
    authority: EstimateAuthority
    eps_consensus: float | None
    revenue_consensus: float | None
    analyst_count: int | None
    eps_high: float | None = None
    eps_low: float | None = None
    revenue_high: float | None = None
    revenue_low: float | None = None
    currency: str | None = None
    source: str = "INVESTINGPRO"

    def __post_init__(self) -> None:
        if not self.ticker.strip():
            raise ValueError("ticker is required")
        require_aware_timestamp(self.fiscal_period_end)
        require_aware_timestamp(self.estimate_at)
        if self.estimate_at > self.fiscal_period_end:
            # allowed in some forward-year estimate tables? no: lock target period end ahead/equal
            pass
        for name, value in (
            ("eps_consensus", self.eps_consensus),
            ("revenue_consensus", self.revenue_consensus),
            ("eps_high", self.eps_high),
            ("eps_low", self.eps_low),
            ("revenue_high", self.revenue_high),
            ("revenue_low", self.revenue_low),
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite when provided")
        if self.analyst_count is not None and self.analyst_count < 0:
            raise ValueError("analyst_count cannot be negative")
        if self.authority is EstimateAuthority.HISTORICAL_PIT and not self.source.strip():
            raise ValueError("historical PIT estimate requires source")


@dataclass(frozen=True)
class EstimateRevision:
    ticker: str
    fiscal_period_end: datetime
    earlier_at: datetime
    later_at: datetime
    eps_revision: float | None
    revenue_revision: float | None

    def __post_init__(self) -> None:
        require_aware_timestamp(self.fiscal_period_end)
        require_aware_timestamp(self.earlier_at)
        require_aware_timestamp(self.later_at)
        if self.earlier_at >= self.later_at:
            raise ValueError("revision snapshots must be chronological")


def compute_revision(
    earlier: AnalystEstimateSnapshot,
    later: AnalystEstimateSnapshot,
) -> EstimateRevision:
    if earlier.ticker != later.ticker:
        raise ValueError("revision ticker mismatch")
    if earlier.fiscal_period_end != later.fiscal_period_end:
        raise ValueError("revision fiscal period mismatch")
    if earlier.authority is not EstimateAuthority.HISTORICAL_PIT:
        raise ValueError("earlier snapshot must be historical PIT")
    if later.authority is not EstimateAuthority.HISTORICAL_PIT:
        raise ValueError("later snapshot must be historical PIT")
    if earlier.estimate_at >= later.estimate_at:
        raise ValueError("revision snapshots must be chronological")

    eps_revision = None
    if earlier.eps_consensus is not None and later.eps_consensus is not None:
        eps_revision = later.eps_consensus - earlier.eps_consensus

    revenue_revision = None
    if earlier.revenue_consensus is not None and later.revenue_consensus is not None:
        revenue_revision = later.revenue_consensus - earlier.revenue_consensus

    return EstimateRevision(
        ticker=earlier.ticker,
        fiscal_period_end=earlier.fiscal_period_end,
        earlier_at=earlier.estimate_at,
        later_at=later.estimate_at,
        eps_revision=eps_revision,
        revenue_revision=revenue_revision,
    )


def require_historical_estimate(snapshot: AnalystEstimateSnapshot) -> None:
    if snapshot.authority is not EstimateAuthority.HISTORICAL_PIT:
        raise ValueError("current-only estimate cannot be backfilled into historical PIT")
