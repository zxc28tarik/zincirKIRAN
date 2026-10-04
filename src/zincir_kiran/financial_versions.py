"""Financial revision/version authority for strict PIT research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .pit import require_aware_timestamp


class VersionAuthority(StrEnum):
    AUTHORITATIVE_PIT = "AUTHORITATIVE_PIT"
    EXPERIMENTAL_VERSION_RISK = "EXPERIMENTAL_VERSION_RISK"
    BULK_LATEST_ONLY = "BULK_LATEST_ONLY"


@dataclass(frozen=True)
class FinancialVersion:
    ticker: str
    period_end: str
    disclosure_id: str
    published_at: datetime
    raw_sha256: str
    version_sequence: int
    version_tag: str
    supersedes_disclosure_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("ticker", self.ticker),
            ("period_end", self.period_end),
            ("disclosure_id", self.disclosure_id),
            ("raw_sha256", self.raw_sha256),
            ("version_tag", self.version_tag),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.published_at)
        if len(self.raw_sha256) != 64:
            raise ValueError("raw_sha256 must be 64 hex chars")
        int(self.raw_sha256, 16)
        if self.version_sequence < 1:
            raise ValueError("version_sequence must be >= 1")
        if self.supersedes_disclosure_id == self.disclosure_id:
            raise ValueError("version cannot supersede itself")


@dataclass(frozen=True)
class FinancialVersionChain:
    ticker: str
    period_end: str
    versions: tuple[FinancialVersion, ...]
    enumeration_complete: bool
    authority: VersionAuthority

    def __post_init__(self) -> None:
        if not self.ticker.strip() or not self.period_end.strip():
            raise ValueError("ticker and period_end are required")
        if not self.versions:
            raise ValueError("version chain cannot be empty")
        if self.versions != tuple(
            sorted(
                self.versions,
                key=lambda item: (item.published_at, item.version_sequence, item.disclosure_id),
            )
        ):
            raise ValueError("versions must be sorted chronologically")
        ids = [item.disclosure_id for item in self.versions]
        if len(ids) != len(set(ids)):
            raise ValueError("disclosure_id values must be unique")
        for item in self.versions:
            if item.ticker != self.ticker or item.period_end != self.period_end:
                raise ValueError("all versions must belong to the same ticker/period")
        if self.authority is VersionAuthority.AUTHORITATIVE_PIT and not self.enumeration_complete:
            raise ValueError("authoritative PIT requires complete version enumeration")
        if self.authority is VersionAuthority.BULK_LATEST_ONLY and len(self.versions) != 1:
            raise ValueError("BULK_LATEST_ONLY chain must contain only the observed latest version")


def select_version_at_cutoff(
    chain: FinancialVersionChain,
    *,
    cutoff_at: datetime,
) -> FinancialVersion | None:
    require_aware_timestamp(cutoff_at)
    if chain.authority is not VersionAuthority.AUTHORITATIVE_PIT:
        raise ValueError("cutoff selection requires AUTHORITATIVE_PIT version chain")
    visible = [item for item in chain.versions if item.published_at <= cutoff_at]
    if not visible:
        return None
    return visible[-1]


def require_authoritative_factor_input(chain: FinancialVersionChain) -> None:
    if chain.authority is not VersionAuthority.AUTHORITATIVE_PIT:
        raise ValueError("financial statement is not authorized for authoritative PIT factor input")
    if not chain.enumeration_complete:
        raise ValueError("financial version enumeration is incomplete")


def korts_2022_revision_fixture() -> FinancialVersionChain:
    """Real KAP P7 regression case proving that bulk latest-only is insufficient."""
    from datetime import timezone, timedelta

    tz = timezone(timedelta(hours=3))
    original = FinancialVersion(
        ticker="KORTS",
        period_end="2022-12-31",
        disclosure_id="1122417",
        published_at=datetime(2023, 3, 9, 18, 36, 13, tzinfo=tz),
        raw_sha256="1" * 64,
        version_sequence=1,
        version_tag="ORIGINAL",
        supersedes_disclosure_id=None,
    )
    correction = FinancialVersion(
        ticker="KORTS",
        period_end="2022-12-31",
        disclosure_id="1126845",
        published_at=datetime(2023, 3, 21, 18, 32, 11, tzinfo=tz),
        raw_sha256="2" * 64,
        version_sequence=2,
        version_tag="CORRECTION",
        supersedes_disclosure_id="1122417",
    )
    return FinancialVersionChain(
        ticker="KORTS",
        period_end="2022-12-31",
        versions=(original, correction),
        enumeration_complete=True,
        authority=VersionAuthority.AUTHORITATIVE_PIT,
    )
