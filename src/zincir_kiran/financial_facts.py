"""Typed financial facts with explicit accounting context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from .accounting import AccountingContext, require_comparable
from .pit import require_aware_timestamp


@dataclass(frozen=True)
class FinancialFact:
    company_id: str
    metric_id: str
    period_end: date
    value: Decimal | None
    available_at: datetime
    accounting: AccountingContext
    revision_id: str

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")
        if not self.metric_id.strip():
            raise ValueError("metric_id is required")
        if not self.revision_id.strip():
            raise ValueError("revision_id is required")
        require_aware_timestamp(self.available_at)


def require_financial_fact_comparison(left: FinancialFact, right: FinancialFact) -> None:
    """Block cross-period feature math when accounting regimes are unsafe."""
    require_comparable(left.accounting, right.accounting)
