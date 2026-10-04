"""Historical KAP financial-disclosure version enumeration contracts.

This module models what the public KAP disclosure query exposes. Successful
window coverage never upgrades the result to authoritative completeness.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class EnumerationStatus(StrEnum):
    ENUMERATION_NOT_RUN = "ENUMERATION_NOT_RUN"
    ENUMERATED_PARTIAL = "ENUMERATED_PARTIAL"
    ENUMERATED_WITH_CORRECTION_CHAINS = "ENUMERATED_WITH_CORRECTION_CHAINS"
    COMPLETE_AUTHORITY_FORBIDDEN = "COMPLETE_AUTHORITY_FORBIDDEN"


@dataclass(frozen=True)
class EnumerationWindow:
    window_id: str
    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ValueError("window_id is required")
        require_aware_timestamp(self.start_at)
        require_aware_timestamp(self.end_at)
        if self.start_at >= self.end_at:
            raise ValueError("enumeration window must be half-open and non-empty")


@dataclass(frozen=True)
class DisclosureVersionRecord:
    disclosure_id: str
    published_at: datetime
    report_year: int | None
    report_period: int | None
    stock_codes: tuple[str, ...]
    modify_status: str | None
    response_sha256: str

    def __post_init__(self) -> None:
        if not self.disclosure_id.strip():
            raise ValueError("disclosure_id is required")
        require_aware_timestamp(self.published_at)
        if self.stock_codes != tuple(sorted(set(self.stock_codes))):
            raise ValueError("stock_codes must be unique and sorted")
        if len(self.response_sha256) != 64:
            raise ValueError("response_sha256 must be 64 hex chars")
        int(self.response_sha256, 16)


@dataclass(frozen=True)
class CorrectionEdge:
    older_disclosure_id: str
    newer_disclosure_id: str
    older_published_at: datetime
    newer_published_at: datetime
    relation_label: str

    def __post_init__(self) -> None:
        if not self.older_disclosure_id.strip() or not self.newer_disclosure_id.strip():
            raise ValueError("correction edge ids are required")
        require_aware_timestamp(self.older_published_at)
        require_aware_timestamp(self.newer_published_at)
        if self.older_published_at >= self.newer_published_at:
            raise ValueError("correction edge must move forward in publication time")
        if not self.relation_label.strip():
            raise ValueError("relation_label is required")


@dataclass(frozen=True)
class EnumerationReceipt:
    run_id: str
    captured_at: datetime
    windows_requested: int
    windows_succeeded: int
    windows_failed: int
    distinct_disclosures: int
    correction_edges: int
    status: EnumerationStatus
    completeness_guaranteed: bool
    blocker_code: str

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.blocker_code.strip():
            raise ValueError("run identity and blocker are required")
        require_aware_timestamp(self.captured_at)
        if min(
            self.windows_requested,
            self.windows_succeeded,
            self.windows_failed,
            self.distinct_disclosures,
            self.correction_edges,
        ) < 0:
            raise ValueError("enumeration counts cannot be negative")
        if self.windows_succeeded + self.windows_failed != self.windows_requested:
            raise ValueError("window accounting must be exhaustive")
        if self.completeness_guaranteed:
            raise ValueError(
                "public KAP query route has no proven completeness guarantee"
            )
        if self.status is EnumerationStatus.COMPLETE_AUTHORITY_FORBIDDEN:
            raise ValueError("COMPLETE_AUTHORITY_FORBIDDEN is a policy sentinel, not a run result")


def validate_unique_disclosures(
    records: tuple[DisclosureVersionRecord, ...],
) -> None:
    seen: dict[str, DisclosureVersionRecord] = {}
    for record in records:
        existing = seen.get(record.disclosure_id)
        if existing is None:
            seen[record.disclosure_id] = record
            continue
        if existing != record:
            raise ValueError(
                f"conflicting payload for duplicate disclosure id {record.disclosure_id}"
            )


def known_w10_correction_edge() -> CorrectionEdge:
    from datetime import UTC

    return CorrectionEdge(
        older_disclosure_id="1122417",
        newer_disclosure_id="1126845",
        older_published_at=datetime(2023, 3, 9, 15, 36, 13, tzinfo=UTC),
        newer_published_at=datetime(2023, 3, 21, 15, 32, 11, tzinfo=UTC),
        relation_label="Düzeltilmiş Bildirim",
    )



def build_monthly_windows(
    *,
    start_year: int,
    start_month: int,
    months: int,
) -> tuple[EnumerationWindow, ...]:
    """Build deterministic UTC half-open month windows."""
    from datetime import UTC

    if months <= 0:
        raise ValueError("months must be positive")
    if not 1 <= start_month <= 12:
        raise ValueError("start_month must be in 1..12")

    rows: list[EnumerationWindow] = []
    year = start_year
    month = start_month
    for _ in range(months):
        next_year = year + (1 if month == 12 else 0)
        next_month = 1 if month == 12 else month + 1
        rows.append(
            EnumerationWindow(
                window_id=f"{year:04d}-{month:02d}",
                start_at=datetime(year, month, 1, tzinfo=UTC),
                end_at=datetime(next_year, next_month, 1, tzinfo=UTC),
            )
        )
        year, month = next_year, next_month
    return tuple(rows)


def zincir_kiran_60_month_enumeration_plan() -> tuple[EnumerationWindow, ...]:
    """Publication-window plan aligned to the 2021-08..2026-07 research horizon."""
    return build_monthly_windows(start_year=2021, start_month=8, months=60)


def classify_enumeration_status(
    *,
    windows_requested: int,
    windows_succeeded: int,
    correction_edges: int,
) -> EnumerationStatus:
    if windows_requested <= 0:
        return EnumerationStatus.ENUMERATION_NOT_RUN
    if windows_succeeded < windows_requested:
        return EnumerationStatus.ENUMERATED_PARTIAL
    if correction_edges > 0:
        return EnumerationStatus.ENUMERATED_WITH_CORRECTION_CHAINS
    return EnumerationStatus.ENUMERATED_PARTIAL
