from datetime import date
from decimal import Decimal

from zincir_kiran.corporate_action_field_contracts import (
    DividendContractStatus,
    DividendShareGroupEconomics,
    OfficialDividendEconomics,
    resolve_cash_dividend_contract,
)


def economics(**overrides):
    values = {
        "event_id": "1509356",
        "target_ticker": "FROTO",
        "currency": "TRY",
        "proposed_ex_date": date(2025, 12, 3),
        "final_ex_date": date(2025, 12, 3),
        "payment_date": date(2025, 12, 5),
        "share_groups": (
            DividendShareGroupEconomics(
                ticker="FROTO",
                gross_cash_per_nominal_try=Decimal("6.05"),
                share_dividend_ratio_percent=Decimal("0"),
            ),
        ),
    }
    values.update(overrides)
    return OfficialDividendEconomics(**values)


def test_complete_cash_dividend_contract_resolves():
    result = resolve_cash_dividend_contract(economics())
    assert result.status is DividendContractStatus.RESOLVED_CASH_DIVIDEND
    assert result.resolved is True
    assert result.gross_cash_per_nominal_try == Decimal("6.05")
    assert result.ex_date == date(2025, 12, 3)


def test_proposed_date_without_final_date_does_not_resolve():
    result = resolve_cash_dividend_contract(
        economics(final_ex_date=None)
    )
    assert result.status is DividendContractStatus.MISSING_FINAL_EX_DATE
    assert result.resolved is False


def test_share_dividend_component_blocks_pure_cash_resolution():
    result = resolve_cash_dividend_contract(
        economics(
            share_groups=(
                DividendShareGroupEconomics(
                    ticker="FROTO",
                    gross_cash_per_nominal_try=Decimal("6.05"),
                    share_dividend_ratio_percent=Decimal("10"),
                ),
            )
        )
    )
    assert result.status is DividendContractStatus.SHARE_DIVIDEND_COMPONENT_PRESENT
    assert result.resolved is False


def test_missing_payment_date_does_not_resolve():
    result = resolve_cash_dividend_contract(economics(payment_date=None))
    assert result.status is DividendContractStatus.MISSING_PAYMENT_DATE


def test_non_try_dividend_does_not_resolve():
    result = resolve_cash_dividend_contract(economics(currency="USD"))
    assert result.status is DividendContractStatus.CURRENCY_NOT_TRY


def test_target_share_group_must_match_exactly_once():
    result = resolve_cash_dividend_contract(
        economics(
            share_groups=(
                DividendShareGroupEconomics(
                    ticker="OTHER",
                    gross_cash_per_nominal_try=Decimal("6.05"),
                    share_dividend_ratio_percent=Decimal("0"),
                ),
            )
        )
    )
    assert result.status is DividendContractStatus.TARGET_SHARE_GROUP_AMBIGUOUS
