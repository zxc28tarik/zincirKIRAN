import pytest

from zincir_kiran.market_bootstrap import (
    MarketBootstrapAuthority,
    default_market_bootstrap_artifacts,
    require_official_borsa,
)


def test_daily_price_corpus_is_large_but_not_official_borsa() -> None:
    daily = next(x for x in default_market_bootstrap_artifacts() if x.artifact_id == "v24-daily-member-prices")
    assert daily.row_count == 271267
    assert daily.authority is MarketBootstrapAuthority.VALIDATED_DERIVED_MARKET_DATA
    with pytest.raises(ValueError, match="not authorized"):
        require_official_borsa(daily)


def test_monthly_execution_panel_is_complete_for_locked_scope() -> None:
    panel = next(x for x in default_market_bootstrap_artifacts() if x.artifact_id == "v24-monthly-execution-panel")
    assert panel.row_count == 6000
    assert panel.coverage_start == "2021-08"
    assert panel.coverage_end == "2026-07"
    assert panel.authority is MarketBootstrapAuthority.VALIDATED_EXECUTION_PANEL


def test_hashes_and_commits_are_fully_pinned() -> None:
    for artifact in default_market_bootstrap_artifacts():
        assert len(artifact.source_commit) == 40
        assert len(artifact.sha256) == 64
