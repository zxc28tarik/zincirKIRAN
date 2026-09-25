from datetime import UTC, date, datetime

import pytest

from zincir_kiran.availability import (
    from_date_only_publication,
    from_exact_publication_timestamp,
)


def test_exact_timestamp_is_preserved() -> None:
    published = datetime(2026, 4, 29, 18, 20, tzinfo=UTC)
    decision = from_exact_publication_timestamp(published)

    assert decision.available_at == published
    assert decision.quality_flag == "VERIFIED"
    assert decision.rule == "EXACT_PUBLICATION_TIMESTAMP"


def test_date_only_publication_defers_to_supplied_next_session() -> None:
    next_session = datetime(2026, 5, 4, 7, 0, tzinfo=UTC)
    decision = from_date_only_publication(
        date(2026, 5, 1),
        next_trading_session=next_session,
    )

    assert decision.available_at == next_session
    assert decision.quality_flag == "ESTIMATED_TIMESTAMP"


def test_date_only_rule_rejects_same_day_session() -> None:
    same_day = datetime(2026, 5, 1, 7, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="after publication_date"):
        from_date_only_publication(
            date(2026, 5, 1),
            next_trading_session=same_day,
        )
