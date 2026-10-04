"""Official/public source acquisition contracts for Zincir Kıran.

This layer records how real evidence was acquired. It does not guess undocumented
endpoints and it does not treat an inaccessible source as successfully acquired.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class AcquisitionStatus(StrEnum):
    ACQUIRED = "ACQUIRED"
    BLOCKED = "BLOCKED"
    MANUAL_EXPORT_REQUIRED = "MANUAL_EXPORT_REQUIRED"


@dataclass(frozen=True)
class OfficialSourceDefinition:
    source_id: str
    name: str
    landing_url: str
    official: bool
    historical_access_note: str
    runtime_dependency_allowed: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("source_id", self.source_id),
            ("name", self.name),
            ("landing_url", self.landing_url),
            ("historical_access_note", self.historical_access_note),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")


OFFICIAL_SOURCES = (
    OfficialSourceDefinition(
        source_id="borsa_istanbul",
        name="Borsa Istanbul",
        landing_url="https://www.borsaistanbul.com/veriler/pay-piyasasi-verileri",
        official=True,
        historical_access_note=(
            "Public market/reference pages expose current and selected historical files; "
            "the exchange directs broader historical data users to DataStore."
        ),
        runtime_dependency_allowed=True,
    ),
    OfficialSourceDefinition(
        source_id="kap",
        name="KAP",
        landing_url="https://kap.org.tr/tr/bildirim-sorgu",
        official=True,
        historical_access_note=(
            "Detailed disclosure search and financial statement query are public surfaces; "
            "acquisition must preserve disclosure/publication timestamps."
        ),
        runtime_dependency_allowed=True,
    ),
)


@dataclass(frozen=True)
class AcquisitionAttempt:
    acquisition_id: str
    source_id: str
    requested_url: str
    attempted_at: datetime
    status: AcquisitionStatus
    blocker_code: str | None = None
    blocker_detail: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("acquisition_id", self.acquisition_id),
            ("source_id", self.source_id),
            ("requested_url", self.requested_url),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.attempted_at)
        if self.status is AcquisitionStatus.ACQUIRED:
            if self.blocker_code is not None or self.blocker_detail is not None:
                raise ValueError("successful acquisition cannot carry blocker metadata")
        else:
            if not self.blocker_code or not self.blocker_code.strip():
                raise ValueError("blocked/manual acquisition requires blocker_code")
            if not self.blocker_detail or not self.blocker_detail.strip():
                raise ValueError("blocked/manual acquisition requires blocker_detail")


@dataclass(frozen=True)
class AcquiredArtifactReceipt:
    acquisition_id: str
    source_id: str
    source_url: str
    retrieved_at: datetime
    content_sha256: str
    byte_size: int
    media_type: str | None

    def __post_init__(self) -> None:
        for name, value in (
            ("acquisition_id", self.acquisition_id),
            ("source_id", self.source_id),
            ("source_url", self.source_url),
            ("content_sha256", self.content_sha256),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.retrieved_at)
        if self.byte_size < 0:
            raise ValueError("byte_size cannot be negative")
        if len(self.content_sha256) != 64:
            raise ValueError("content_sha256 must be SHA-256 hex")
        try:
            int(self.content_sha256, 16)
        except ValueError as exc:
            raise ValueError("content_sha256 must be hexadecimal") from exc

    @classmethod
    def from_bytes(
        cls,
        *,
        acquisition_id: str,
        source_id: str,
        source_url: str,
        retrieved_at: datetime,
        content: bytes,
        media_type: str | None,
    ) -> AcquiredArtifactReceipt:
        return cls(
            acquisition_id=acquisition_id,
            source_id=source_id,
            source_url=source_url,
            retrieved_at=retrieved_at,
            content_sha256=hashlib.sha256(content).hexdigest(),
            byte_size=len(content),
            media_type=media_type,
        )


def official_source_ids() -> set[str]:
    return {item.source_id for item in OFFICIAL_SOURCES}


def validate_acquisition_source(source_id: str) -> OfficialSourceDefinition:
    for item in OFFICIAL_SOURCES:
        if item.source_id == source_id:
            return item
    raise ValueError(f"unknown official/public source: {source_id}")
