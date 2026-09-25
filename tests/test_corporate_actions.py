from datetime import UTC, date, datetime

import pytest

from zincir_kiran.corporate_actions import (
    CorporateAction,
    CorporateActionType,
    visible_actions,
)


def test_future_corporate_action_does_not_leak() -> None:
    action = CorporateAction(
        security_id="MEGMT",
        action_type=CorporateActionType.BONUS_ISSUE,
        announcement_at=datetime(2026, 9, 15, 13, 18, 4, tzinfo=UTC),
        available_at=datetime(2026, 9, 15, 13, 18, 4, tzinfo=UTC),
        ex_date=date(2026, 9, 21),
        record_date=date(2026, 9, 22),
        payment_date=date(2026, 9, 23),
        source_url="https://www.kap.org.tr/tr/Bildirim/1662964",
    )

    before = datetime(2026, 9, 15, 13, 18, 3, tzinfo=UTC)
    at_time = datetime(2026, 9, 15, 13, 18, 4, tzinfo=UTC)

    assert visible_actions([action], before) == ()
    assert visible_actions([action], at_time) == (action,)


def test_corporate_action_rejects_impossible_dates() -> None:
    with pytest.raises(ValueError, match="record_date"):
        CorporateAction(
            security_id="X",
            action_type=CorporateActionType.CASH_DIVIDEND,
            available_at=datetime(2026, 1, 1, tzinfo=UTC),
            ex_date=date(2026, 1, 10),
            record_date=date(2026, 1, 9),
        )
