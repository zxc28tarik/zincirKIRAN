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
