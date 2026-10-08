"""Classify official KAP detail pages by resolution stage, never by alpha result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OfficialDetailStage(StrEnum):
    PROCESS_ONLY = "PROCESS_ONLY"
    ECONOMIC_DETAIL_CANDIDATE = "ECONOMIC_DETAIL_CANDIDATE"
    UNKNOWN = "UNKNOWN"


_PROCESS_ONLY_TITLE_MARKERS = (
    "İZAHNAME (SPK ONAYINA SUNULAN)",
    "SERMAYE ARTIRIMINDAN ELDE EDİLECEK / EDİLEN FONUN KULLANIMINA İLİŞKİN RAPOR",
    "SERMAYE ARTIRIMINDAN ELDE EDİLECEK - EDİLEN FONUN KULLANIMINA İLİŞKİN RAPOR",
)

_ECONOMIC_CANDIDATE_TITLE_MARKERS = (
    "KAR PAYI DAĞITIM İŞLEMLERİNE İLİŞKİN BİLDİRİM",
)


@dataclass(frozen=True)
class OfficialDetailStageEvidence:
    event_id: str
    event_type: str
    title: str
    summary: str | None

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.event_type.strip():
            raise ValueError("event identity is required")


@dataclass(frozen=True)
class OfficialDetailStageResult:
    event_id: str
    stage: OfficialDetailStage
    reason_code: str
    risk_released: bool


def classify_official_detail_stage(
    evidence: OfficialDetailStageEvidence,
) -> OfficialDetailStageResult:
    text = " ".join(
        x for x in (evidence.title, evidence.summary or "") if x
    ).upper()

    if any(marker in text for marker in _PROCESS_ONLY_TITLE_MARKERS):
        return OfficialDetailStageResult(
            event_id=evidence.event_id,
            stage=OfficialDetailStage.PROCESS_ONLY,
            reason_code="OFFICIAL_PROCESS_DOCUMENT_NOT_ECONOMIC_ACTION_DETAIL",
            risk_released=False,
        )

    if any(marker in text for marker in _ECONOMIC_CANDIDATE_TITLE_MARKERS):
        return OfficialDetailStageResult(
            event_id=evidence.event_id,
            stage=OfficialDetailStage.ECONOMIC_DETAIL_CANDIDATE,
            reason_code="OFFICIAL_ECONOMIC_DETAIL_FORM_CANDIDATE",
            risk_released=False,
        )

    return OfficialDetailStageResult(
        event_id=evidence.event_id,
        stage=OfficialDetailStage.UNKNOWN,
        reason_code="OFFICIAL_DETAIL_STAGE_NOT_YET_CONTRACTED",
        risk_released=False,
    )
