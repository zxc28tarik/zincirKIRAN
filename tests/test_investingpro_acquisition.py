from datetime import UTC, datetime

import pytest

from zincir_kiran.investingpro_acquisition import (
    PROHIBITED_AS_TARGETS,
    EstimateMetric,
    EstimateObservation,
    InvestingProAuthority,
    InvestingProExportBatch,
    RosterReconciliation,
    reconcile_ticker_sets,
    require_historical_estimate_use,
)

NOW = datetime(2026, 10, 4, 20, 45, tzinfo=UTC)


def test_screener_export_batch_must_be_under_100_rows() -> None:
    with pytest.raises(ValueError, match="1..99"):
        InvestingProExportBatch(
            batch_id="too-large",
            exported_at=NOW,
            filter_description="Borsa Istanbul",
            row_count=100,
            content_sha256="a" * 64,
            authority=InvestingProAuthority.CURRENT_SCREENER_SNAPSHOT,
        )


def test_current_estimate_snapshot_cannot_backfill_history() -> None:
    observation = EstimateObservation(
        ticker="THYAO",
        metric=EstimateMetric.EPS_ESTIMATE,
        value=10.0,
        observed_at=NOW,
        period_label="FY2027",
        source_batch_id="batch-1",
        authority=InvestingProAuthority.CURRENT_ESTIMATE_SNAPSHOT,
    )
    with pytest.raises(ValueError, match="cannot be backfilled"):
        require_historical_estimate_use(observation)


def test_timestamped_revision_history_can_be_used_historically() -> None:
    observation = EstimateObservation(
        ticker="THYAO",
        metric=EstimateMetric.EPS_REVISION,
        value=0.04,
        observed_at=NOW,
        period_label="FY2027",
        source_batch_id="batch-2",
        authority=InvestingProAuthority.TIMESTAMPED_REVISION_HISTORY,
    )
    require_historical_estimate_use(observation)


def test_export_receipt_hashes_exact_bytes() -> None:
    batch = InvestingProExportBatch.from_bytes(
        batch_id="batch-1",
        exported_at=NOW,
        filter_description="Turkey | Borsa Istanbul | Primary Trading Item",
        row_count=98,
        content=b"exact export bytes",
        authority=InvestingProAuthority.CURRENT_SCREENER_SNAPSHOT,
    )
    assert len(batch.content_sha256) == 64
    assert batch.row_count == 98


def test_roster_reconciliation_rejects_impossible_match_count() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        RosterReconciliation(
            kap_roster_count=807,
            investingpro_unique_primary_count=900,
            matched_tickers=808,
            kap_only=0,
            investingpro_only=92,
            duplicate_primary_items=0,
        )


def test_ai_and_fair_value_products_are_not_targets() -> None:
    assert "FAIR_VALUE" in PROHIBITED_AS_TARGETS
    assert "PROPICKS_AI" in PROHIBITED_AS_TARGETS
    assert "HEALTH_SCORE" in PROHIBITED_AS_TARGETS


def test_roster_reconciliation_counts_duplicates_and_source_gaps() -> None:
    result = reconcile_ticker_sets(
        kap_tickers={"AAA", "BBB", "CCC"},
        investingpro_tickers=["AAA", "BBB", "BBB", "DDD"],
    )
    assert result.kap_roster_count == 3
    assert result.investingpro_unique_primary_count == 3
    assert result.matched_tickers == 2
    assert result.kap_only == 1
    assert result.investingpro_only == 1
    assert result.duplicate_primary_items == 1
