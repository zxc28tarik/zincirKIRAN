import pytest

from zincir_kiran.current_bootstrap import (
    CurrentEvidenceAuthority,
    current_bootstrap_artifacts,
    require_historical_use,
)


def test_current_roster_is_discovery_only() -> None:
    roster = next(x for x in current_bootstrap_artifacts() if x.artifact_id == "current-kap-bist-roster")
    assert roster.row_count == 807
    assert roster.authority is CurrentEvidenceAuthority.CURRENT_ROSTER_DISCOVERY_ONLY


def test_current_share_basis_has_528_usable_rows() -> None:
    share = next(x for x in current_bootstrap_artifacts() if x.artifact_id == "current-explicit-share-basis")
    assert share.row_count == 528
    assert share.authority is CurrentEvidenceAuthority.CURRENT_SHARE_STATE_EVIDENCE


def test_current_raw_close_has_629_rows() -> None:
    close = next(x for x in current_bootstrap_artifacts() if x.artifact_id == "current-raw-close")
    assert close.row_count == 629
    assert close.authority is CurrentEvidenceAuthority.CURRENT_MARKET_SNAPSHOT


def test_current_artifacts_cannot_backfill_history() -> None:
    for artifact in current_bootstrap_artifacts():
        with pytest.raises(ValueError, match="cannot be used for historical backfill"):
            require_historical_use(artifact)
