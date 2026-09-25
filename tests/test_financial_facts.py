from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from zincir_kiran.accounting import AccountingContext, RestatementStatus
from zincir_kiran.financial_facts import FinancialFact, require_financial_fact_comparison


def fact(*, inflation_adjusted: bool | None) -> FinancialFact:
    return FinancialFact(
        company_id="COMPANY",
        metric_id="revenue",
        period_end=date(2025, 12, 31),
        value=Decimal(100),
        available_at=datetime(2026, 3, 1, tzinfo=UTC),
        accounting=AccountingContext(
            reporting_standard="TFRS",
            inflation_adjusted=inflation_adjusted,
            restatement_status=RestatementStatus.RESTATED,
        ),
        revision_id="r1",
    )


def test_financial_fact_carries_explicit_accounting_context() -> None:
    row = fact(inflation_adjusted=True)
    assert row.accounting.reporting_standard == "TFRS"
    assert row.accounting.inflation_adjusted is True


def test_financial_fact_comparison_blocks_regime_mismatch() -> None:
    with pytest.raises(ValueError, match="INCOMPATIBLE"):
        require_financial_fact_comparison(
            fact(inflation_adjusted=True),
            fact(inflation_adjusted=False),
        )


def test_financial_fact_comparison_blocks_missing_regime() -> None:
    with pytest.raises(ValueError, match="UNDECIDED"):
        require_financial_fact_comparison(
            fact(inflation_adjusted=None),
            fact(inflation_adjusted=True),
        )
