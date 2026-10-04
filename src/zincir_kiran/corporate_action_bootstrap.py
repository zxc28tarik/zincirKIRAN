"""Evidence-scoped corporate-action bootstrap from historical KAP inventory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .corporate_actions import CorporateActionType
from .pit import require_aware_timestamp


class BootstrapAuthority(StrEnum):
    POSITIVE_EVENT_EVIDENCE = "POSITIVE_EVENT_EVIDENCE"
    COVERED_WINDOW_ABSENCE_EVIDENCE = "COVERED_WINDOW_ABSENCE_EVIDENCE"
    OFFICIAL_BORSA_LINEAGE = "OFFICIAL_BORSA_LINEAGE"


class BootstrapEventType(StrEnum):
    CAPITAL_INCREASE = "CAPITAL_INCREASE"
    CAPITAL_DECREASE = "CAPITAL_DECREASE"
    MERGER = "MERGER"
    DEMERGER = "DEMERGER"
    SHARE_CLASS_CHANGE = "SHARE_CLASS_CHANGE"
    TICKER_CHANGE = "TICKER_CHANGE"
    AMBIGUOUS_SHARE_COUNT_ACTION = "AMBIGUOUS_SHARE_COUNT_ACTION"


@dataclass(frozen=True)
class CorporateActionEvidence:
    event_id: str
    published_at: datetime
    ticker: str
    subject: str
    event_type: BootstrapEventType
    authority: BootstrapAuthority
    source_sha256: str
    source_system: str

    def __post_init__(self) -> None:
        for name, value in (
            ("event_id", self.event_id),
            ("ticker", self.ticker),
            ("subject", self.subject),
            ("source_system", self.source_system),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        require_aware_timestamp(self.published_at)
        if len(self.source_sha256) != 64:
            raise ValueError("source_sha256 must be 64 hex chars")
        int(self.source_sha256, 16)


@dataclass(frozen=True)
class CoveredInventoryWindow:
    start_at: datetime
    end_at: datetime
    complete: bool
    source_manifest_sha256: str

    def __post_init__(self) -> None:
        require_aware_timestamp(self.start_at)
        require_aware_timestamp(self.end_at)
        if self.start_at > self.end_at:
            raise ValueError("covered window start must not exceed end")
        if len(self.source_manifest_sha256) != 64:
            raise ValueError("source manifest sha256 must be 64 hex chars")
        int(self.source_manifest_sha256, 16)


def classify_share_count_subject(subject: str) -> BootstrapEventType | None:
    text = subject.casefold()
    matches: list[BootstrapEventType] = []

    if "sermaye artır" in text:
        matches.append(BootstrapEventType.CAPITAL_INCREASE)
    if "sermaye azalt" in text:
        matches.append(BootstrapEventType.CAPITAL_DECREASE)
    if "birleşme" in text:
        matches.append(BootstrapEventType.MERGER)
    if "bölünme" in text:
        matches.append(BootstrapEventType.DEMERGER)
    if "pay grubu" in text:
        matches.append(BootstrapEventType.SHARE_CLASS_CHANGE)

    unique = tuple(dict.fromkeys(matches))
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return BootstrapEventType.AMBIGUOUS_SHARE_COUNT_ACTION


def production_action_type(
    event_type: BootstrapEventType,
) -> CorporateActionType | None:
    mapping = {
        BootstrapEventType.MERGER: CorporateActionType.MERGER,
        BootstrapEventType.DEMERGER: CorporateActionType.DEMERGER,
        BootstrapEventType.TICKER_CHANGE: CorporateActionType.TICKER_CHANGE,
    }
    return mapping.get(event_type)


def require_absence_authority(window: CoveredInventoryWindow) -> None:
    if not window.complete:
        raise ValueError("historical absence requires a complete covered window")


def require_official_ticker_change(event: CorporateActionEvidence) -> None:
    if event.event_type is not BootstrapEventType.TICKER_CHANGE:
        raise ValueError("event is not a ticker change")
    if event.authority is not BootstrapAuthority.OFFICIAL_BORSA_LINEAGE:
        raise ValueError("ticker change requires official Borsa lineage authority")
