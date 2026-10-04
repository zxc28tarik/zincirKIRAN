from datetime import UTC, datetime

import pytest

from zincir_kiran.analyst_revisions import (
    AnalystEstimateSnapshot,
    EstimateAuthority,
    compute_revision,
    require_historical_estimate,
)


def snap(*, authority: EstimateAuthority, at: datetime, eps=10.0, rev=100.0):
    return AnalystEstimateSnapshot(
        ticker="THYAO",
        fiscal_period_end=datetime(2027, 12, 31, tzinfo=UTC),
        estimate_at=at,
        authority=authority,
        eps_consensus=eps,
        revenue_consensus=rev,
        analyst_count=12,
    )


def test_current_only_estimate_cannot_backfill_history() -> None:
    current = snap(authority=EstimateAuthority.CURRENT_ONLY, at=datetime(2026, 10, 5, tzinfo=UTC))
    with pytest.raises(ValueError, match="cannot be backfilled"):
        require_historical_estimate(current)


def test_revision_requires_two_historical_snapshots() -> None:
    earlier = snap(authority=EstimateAuthority.HISTORICAL_PIT, at=datetime(2026, 8, 1, tzinfo=UTC))
    later = snap(authority=EstimateAuthority.HISTORICAL_PIT, at=datetime(2026, 9, 1, tzinfo=UTC), eps=11.5, rev=105.0)
    revision = compute_revision(earlier, later)
    assert revision.eps_revision == pytest.approx(1.5)
    assert revision.revenue_revision == pytest.approx(5.0)


def test_current_snapshot_cannot_form_historical_revision() -> None:
    earlier = snap(authority=EstimateAuthority.HISTORICAL_PIT, at=datetime(2026, 8, 1, tzinfo=UTC))
    later = snap(authority=EstimateAuthority.CURRENT_ONLY, at=datetime(2026, 9, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="later snapshot must be historical PIT"):
        compute_revision(earlier, later)


def test_revision_requires_same_period() -> None:
    earlier = snap(authority=EstimateAuthority.HISTORICAL_PIT, at=datetime(2026, 8, 1, tzinfo=UTC))
    later = AnalystEstimateSnapshot(
        ticker="THYAO",
        fiscal_period_end=datetime(2028, 12, 31, tzinfo=UTC),
        estimate_at=datetime(2026, 9, 1, tzinfo=UTC),
        authority=EstimateAuthority.HISTORICAL_PIT,
        eps_consensus=11.0,
        revenue_consensus=101.0,
        analyst_count=10,
    )
    with pytest.raises(ValueError, match="fiscal period mismatch"):
        compute_revision(earlier, later)
