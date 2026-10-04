import pytest

from zincir_kiran.kap_bulk_bootstrap import (
    KapArchiveAuthority,
    drifted_archives,
    kap_bulk_archives_v1,
    require_authoritative_historical_pit,
)


def test_bulk_manifest_has_28_archives() -> None:
    rows = kap_bulk_archives_v1()
    assert len(rows) == 28
    assert rows[0].year == 2019
    assert rows[0].period == "9A"
    assert rows[-1].year == 2026
    assert rows[-1].period == "6A"


def test_all_archives_are_official_kap_routes_and_raw_evidence() -> None:
    for row in kap_bulk_archives_v1():
        assert row.download_url.startswith("https://kap.org.tr/tr/api/financialTable/download/")
        assert row.authority is KapArchiveAuthority.RAW_EVIDENCE
        assert len(row.sha256) == 64


def test_only_two_archives_show_manifest_drift() -> None:
    drift = drifted_archives()
    assert [(x.year, x.period) for x in drift] == [(2025, "Y"), (2026, "6A")]


def test_bulk_archive_cannot_be_promoted_to_authoritative_historical_pit() -> None:
    with pytest.raises(ValueError, match="raw evidence only"):
        require_authoritative_historical_pit(kap_bulk_archives_v1()[0])
