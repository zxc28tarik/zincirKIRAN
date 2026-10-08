"""Action-type-specific official economic field contracts for corporate-action resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class DividendContractStatus(StrEnum):
    RESOLVED_CASH_DIVIDEND = "RESOLVED_CASH_DIVIDEND"
    MISSING_FINAL_EX_DATE = "MISSING_FINAL_EX_DATE"
    MISSING_GROSS_CASH_PER_SHARE = "MISSING_GROSS_CASH_PER_SHARE"
    MISSING_PAYMENT_DATE = "MISSING_PAYMENT_DATE"
    CURRENCY_NOT_TRY = "CURRENCY_NOT_TRY"
    SHARE_DIVIDEND_COMPONENT_PRESENT = "SHARE_DIVIDEND_COMPONENT_PRESENT"
    TARGET_SHARE_GROUP_AMBIGUOUS = "TARGET_SHARE_GROUP_AMBIGUOUS"


@dataclass(frozen=True)
class DividendShareGroupEconomics:
    ticker: str
    gross_cash_per_nominal_try: Decimal | None
    share_dividend_ratio_percent: Decimal | None

    def __post_init__(self) -> None:
        if not self.ticker.strip():
            raise ValueError("share-group ticker is required")
        if (
            self.gross_cash_per_nominal_try is not None
            and self.gross_cash_per_nominal_try < 0
        ):
            raise ValueError("gross cash per share cannot be negative")
        if (
            self.share_dividend_ratio_percent is not None
            and self.share_dividend_ratio_percent < 0
        ):
            raise ValueError("share dividend ratio cannot be negative")


@dataclass(frozen=True)
class OfficialDividendEconomics:
    event_id: str
    target_ticker: str
    currency: str | None
    proposed_ex_date: date | None
    final_ex_date: date | None
    payment_date: date | None
    share_groups: tuple[DividendShareGroupEconomics, ...]

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.target_ticker.strip():
            raise ValueError("event_id and target_ticker are required")
        if not self.share_groups:
            raise ValueError("at least one share group is required")


@dataclass(frozen=True)
class DividendContractResult:
    event_id: str
    target_ticker: str
    status: DividendContractStatus
    resolved: bool
    gross_cash_per_nominal_try: Decimal | None
    ex_date: date | None
    payment_date: date | None
    reason_codes: tuple[str, ...]


def resolve_cash_dividend_contract(
    economics: OfficialDividendEconomics,
) -> DividendContractResult:
    matching = [
        group
        for group in economics.share_groups
        if group.ticker.strip().upper() == economics.target_ticker.strip().upper()
    ]
    if len(matching) != 1:
        return DividendContractResult(
            event_id=economics.event_id,
            target_ticker=economics.target_ticker,
            status=DividendContractStatus.TARGET_SHARE_GROUP_AMBIGUOUS,
            resolved=False,
            gross_cash_per_nominal_try=None,
            ex_date=None,
            payment_date=None,
            reason_codes=("TARGET_SHARE_GROUP_MUST_MATCH_EXACTLY_ONCE",),
        )

    group = matching[0]
    if economics.currency != "TRY":
        status = DividendContractStatus.CURRENCY_NOT_TRY
        reasons = ("DIVIDEND_CURRENCY_MUST_BE_TRY",)
    elif economics.final_ex_date is None:
        status = DividendContractStatus.MISSING_FINAL_EX_DATE
        reasons = ("FINAL_EX_DATE_REQUIRED_PROPOSED_DATE_IS_INSUFFICIENT",)
    elif group.gross_cash_per_nominal_try is None:
        status = DividendContractStatus.MISSING_GROSS_CASH_PER_SHARE
        reasons = ("GROSS_CASH_PER_NOMINAL_SHARE_REQUIRED",)
    elif economics.payment_date is None:
        status = DividendContractStatus.MISSING_PAYMENT_DATE
        reasons = ("PAYMENT_DATE_REQUIRED",)
    elif (
        group.share_dividend_ratio_percent is None
        or group.share_dividend_ratio_percent != Decimal("0")
    ):
        status = DividendContractStatus.SHARE_DIVIDEND_COMPONENT_PRESENT
        reasons = (
            "PURE_CASH_CONTRACT_REQUIRES_EXPLICIT_ZERO_SHARE_DIVIDEND_COMPONENT",
        )
    else:
        status = DividendContractStatus.RESOLVED_CASH_DIVIDEND
        reasons = ("OFFICIAL_CASH_DIVIDEND_ECONOMICS_COMPLETE",)

    resolved = status is DividendContractStatus.RESOLVED_CASH_DIVIDEND
    return DividendContractResult(
        event_id=economics.event_id,
        target_ticker=economics.target_ticker,
        status=status,
        resolved=resolved,
        gross_cash_per_nominal_try=(
            group.gross_cash_per_nominal_try if resolved else None
        ),
        ex_date=economics.final_ex_date if resolved else None,
        payment_date=economics.payment_date if resolved else None,
        reason_codes=reasons,
    )
