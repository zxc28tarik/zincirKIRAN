"""Fail-closed corporate-action economic resolution ladder."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EconomicResolutionStatus(StrEnum):
    OFFICIAL_ECONOMIC_ACTION_RESOLVED = "OFFICIAL_ECONOMIC_ACTION_RESOLVED"
    OFFICIAL_NON_PRICE_AFFECTING_PROCESS_RESOLVED = (
        "OFFICIAL_NON_PRICE_AFFECTING_PROCESS_RESOLVED"
    )
    VENDOR_CORROBORATED_ONLY = "VENDOR_CORROBORATED_ONLY"
    UNRESOLVED_OFFICIAL_DETAIL_INSUFFICIENT = (
        "UNRESOLVED_OFFICIAL_DETAIL_INSUFFICIENT"
    )
    UNRESOLVED_OFFICIAL_DETAIL_MISSING = "UNRESOLVED_OFFICIAL_DETAIL_MISSING"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"


@dataclass(frozen=True)
class ShareMultiplierContractEvidence:
    """Official fields required to resolve bonus/split share-multiplier economics."""

    exact_listed_ticker_share_group_once: bool
    effective_date: str | None
    effective_date_finalized: bool
    share_multiplier: float | None
    bonus_rate_percent: float | None

    def __post_init__(self) -> None:
        if self.share_multiplier is not None and self.share_multiplier <= 0:
            raise ValueError("share_multiplier must be positive")
        if self.bonus_rate_percent is not None and self.bonus_rate_percent < 0:
            raise ValueError("bonus_rate_percent cannot be negative")


@dataclass(frozen=True)
class ShareMultiplierContractResult:
    complete: bool
    reason_codes: tuple[str, ...]


def evaluate_share_multiplier_contract(
    evidence: ShareMultiplierContractEvidence,
) -> ShareMultiplierContractResult:
    """Evaluate the locked official share-multiplier contract.

    Vendor data is intentionally absent: vendor evidence can corroborate but can
    never satisfy this official economic contract.
    """

    reasons: list[str] = []
    if not evidence.exact_listed_ticker_share_group_once:
        reasons.append("TARGET_SHARE_GROUP_NOT_EXACTLY_MATCHED_ONCE")
    if not evidence.effective_date or not evidence.effective_date.strip():
        reasons.append("FINAL_EFFECTIVE_DATE_MISSING")
    elif not evidence.effective_date_finalized:
        reasons.append("EFFECTIVE_DATE_NOT_FINALIZED")

    mechanics_present = False
    if (
        evidence.share_multiplier is not None
        and abs(evidence.share_multiplier - 1.0) > 1e-12
    ):
        mechanics_present = True
    if evidence.bonus_rate_percent is not None and evidence.bonus_rate_percent > 0:
        mechanics_present = True
    if not mechanics_present:
        reasons.append("SHARE_MULTIPLIER_OR_BONUS_MECHANICS_MISSING")

    return ShareMultiplierContractResult(
        complete=not reasons,
        reason_codes=tuple(sorted(reasons)),
    )


@dataclass(frozen=True)
class EconomicResolutionEvidence:
    event_id: str
    event_type: str
    official_detail_captured: bool
    official_detail_sha256: str | None
    official_economic_fields_complete: bool
    official_non_price_affecting_explicit: bool
    vendor_corroboration_present: bool
    source_conflict: bool

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.event_type.strip():
            raise ValueError("event_id and event_type are required")
        if self.official_detail_captured:
            if not self.official_detail_sha256:
                raise ValueError(
                    "captured official detail requires content SHA256"
                )
            if len(self.official_detail_sha256) != 64:
                raise ValueError("official_detail_sha256 must be 64 hex")
            try:
                int(self.official_detail_sha256, 16)
            except ValueError as exc:
                raise ValueError(
                    "official_detail_sha256 must be hexadecimal"
                ) from exc
        elif self.official_detail_sha256 is not None:
            raise ValueError(
                "uncaptured official detail cannot carry a SHA256"
            )
        if (
            self.official_economic_fields_complete
            or self.official_non_price_affecting_explicit
        ) and not self.official_detail_captured:
            raise ValueError(
                "official resolution claims require captured official detail"
            )
        if (
            self.official_economic_fields_complete
            and self.official_non_price_affecting_explicit
        ):
            raise ValueError(
                "economic and non-price-affecting resolutions are exclusive"
            )


@dataclass(frozen=True)
class EconomicResolutionResult:
    event_id: str
    status: EconomicResolutionStatus
    risk_released: bool
    vendor_only: bool
    reason_codes: tuple[str, ...]
    shadow_signal_allowed: bool


def resolve_economic_action(
    evidence: EconomicResolutionEvidence,
) -> EconomicResolutionResult:
    reasons: list[str] = []

    if evidence.source_conflict:
        status = EconomicResolutionStatus.SOURCE_CONFLICT
        reasons.append("OFFICIAL_VENDOR_OR_INTERNAL_SOURCE_CONFLICT")
    elif not evidence.official_detail_captured:
        status = EconomicResolutionStatus.UNRESOLVED_OFFICIAL_DETAIL_MISSING
        reasons.append("OFFICIAL_DETAIL_NOT_CAPTURED")
    elif evidence.official_economic_fields_complete:
        status = EconomicResolutionStatus.OFFICIAL_ECONOMIC_ACTION_RESOLVED
        reasons.append("OFFICIAL_ECONOMIC_FIELDS_COMPLETE")
    elif evidence.official_non_price_affecting_explicit:
        status = (
            EconomicResolutionStatus.OFFICIAL_NON_PRICE_AFFECTING_PROCESS_RESOLVED
        )
        reasons.append("OFFICIAL_NON_PRICE_AFFECTING_EXPLICIT")
    elif evidence.vendor_corroboration_present:
        status = EconomicResolutionStatus.VENDOR_CORROBORATED_ONLY
        reasons.append("VENDOR_CORROBORATION_CANNOT_RESOLVE_ALONE")
    else:
        status = (
            EconomicResolutionStatus.UNRESOLVED_OFFICIAL_DETAIL_INSUFFICIENT
        )
        reasons.append("OFFICIAL_DETAIL_INSUFFICIENT_FOR_ECONOMIC_RESOLUTION")

    released = status in {
        EconomicResolutionStatus.OFFICIAL_ECONOMIC_ACTION_RESOLVED,
        EconomicResolutionStatus.OFFICIAL_NON_PRICE_AFFECTING_PROCESS_RESOLVED,
    }
    return EconomicResolutionResult(
        event_id=evidence.event_id,
        status=status,
        risk_released=released,
        vendor_only=status
        is EconomicResolutionStatus.VENDOR_CORROBORATED_ONLY,
        reason_codes=tuple(sorted(reasons)),
        # 45F resolves event evidence only. It cannot emit a shadow signal.
        shadow_signal_allowed=False,
    )
