"""InvestingPro export acquisition contracts for estimates/revisions and all-BIST expansion."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class InvestingProAuthority(StrEnum):
    CURRENT_SCREENER_SNAPSHOT = "CURRENT_SCREENER_SNAPSHOT"
    CURRENT_ESTIMATE_SNAPSHOT = "CURRENT_ESTIMATE_SNAPSHOT"
    TIMESTAMPED_REVISION_HISTORY = "TIMESTAMPED_REVISION_HISTORY"
    FUNDAMENTAL_CROSSCHECK = "FUNDAMENTAL_CROSSCHECK"


class EstimateMetric(StrEnum):
    EPS_ESTIMATE = "EPS_ESTIMATE"
    REVENUE_ESTIMATE = "REVENUE_ESTIMATE"
    EPS_REVISION = "EPS_REVISION"
    REVENUE_REVISION = "REVENUE_REVISION"
    ANALYST_COUNT = "ANALYST_COUNT"
    ESTIMATE_DISPERSION = "ESTIMATE_DISPERSION"
    FORWARD_EPS = "FORWARD_EPS"
    FORWARD_REVENUE = "FORWARD_REVENUE"


@dataclass(frozen=True)
class InvestingProExportBatch:
    batch_id: str
    exported_at: datetime
    filter_description: str
    row_count: int
    content_sha256: str
    authority: InvestingProAuthority

    def __post_init__(self) -> None:
        for name, value in (
            ("batch_id", self.batch_id),
            ("filter_description", self.filter_description),
            ("content_sha256", self.content_sha256),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.exported_at)
        if not 1 <= self.row_count < 100:
            raise ValueError("InvestingPro screener export batch must contain 1..99 rows")
        if len(self.content_sha256) != 64:
            raise ValueError("content_sha256 must be 64 hex chars")
        int(self.content_sha256, 16)

    @classmethod
    def from_bytes(
        cls,
        *,
        batch_id: str,
        exported_at: datetime,
        filter_description: str,
        row_count: int,
        content: bytes,
        authority: InvestingProAuthority,
    ) -> InvestingProExportBatch:
        return cls(
            batch_id=batch_id,
            exported_at=exported_at,
            filter_description=filter_description,
            row_count=row_count,
            content_sha256=hashlib.sha256(content).hexdigest(),
            authority=authority,
        )


@dataclass(frozen=True)
class EstimateObservation:
    ticker: str
    metric: EstimateMetric
    value: float
    observed_at: datetime
    period_label: str | None
    source_batch_id: str
    authority: InvestingProAuthority

    def __post_init__(self) -> None:
        if not self.ticker.strip() or not self.source_batch_id.strip():
            raise ValueError("ticker and source_batch_id are required")
        require_aware_timestamp(self.observed_at)


def require_historical_estimate_use(observation: EstimateObservation) -> None:
    if observation.authority is not InvestingProAuthority.TIMESTAMPED_REVISION_HISTORY:
        raise ValueError(
            "current InvestingPro estimate snapshot cannot be backfilled into historical PIT"
        )


@dataclass(frozen=True)
class RosterReconciliation:
    kap_roster_count: int
    investingpro_unique_primary_count: int
    matched_tickers: int
    kap_only: int
    investingpro_only: int
    duplicate_primary_items: int

    def __post_init__(self) -> None:
        for name, value in (
            ("kap_roster_count", self.kap_roster_count),
            ("investingpro_unique_primary_count", self.investingpro_unique_primary_count),
            ("matched_tickers", self.matched_tickers),
            ("kap_only", self.kap_only),
            ("investingpro_only", self.investingpro_only),
            ("duplicate_primary_items", self.duplicate_primary_items),
        ):
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.matched_tickers > self.kap_roster_count:
            raise ValueError("matched_tickers cannot exceed KAP roster count")


PROHIBITED_AS_TARGETS = (
    "FAIR_VALUE",
    "HEALTH_SCORE",
    "PROPICKS_AI",
    "PROTIPS_SCORE",
    "INVESTINGPRO_RATING",
)



def reconcile_ticker_sets(
    *,
    kap_tickers: set[str],
    investingpro_tickers: list[str],
) -> RosterReconciliation:
    normalized_kap = {ticker.strip().upper() for ticker in kap_tickers if ticker.strip()}
    normalized_ip = [ticker.strip().upper() for ticker in investingpro_tickers if ticker.strip()]
    unique_ip = set(normalized_ip)
    duplicate_primary_items = len(normalized_ip) - len(unique_ip)
    matched = normalized_kap & unique_ip
    return RosterReconciliation(
        kap_roster_count=len(normalized_kap),
        investingpro_unique_primary_count=len(unique_ip),
        matched_tickers=len(matched),
        kap_only=len(normalized_kap - unique_ip),
        investingpro_only=len(unique_ip - normalized_kap),
        duplicate_primary_items=duplicate_primary_items,
    )
