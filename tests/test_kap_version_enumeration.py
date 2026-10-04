from datetime import UTC, datetime

import pytest

from zincir_kiran.kap_version_enumeration import (
    CorrectionEdge,
    DisclosureVersionRecord,
    EnumerationReceipt,
    EnumerationStatus,
    classify_enumeration_status,
    known_w10_correction_edge,
    validate_unique_disclosures,
    zincir_kiran_60_month_enumeration_plan,
)


def test_window_plan_has_exact_60_months() -> None:
    rows = zincir_kiran_60_month_enumeration_plan()
    assert len(rows) == 60
    assert rows[0].window_id == "2021-08"
    assert rows[-1].window_id == "2026-07"


def test_known_w10_edge_moves_forward_in_time() -> None:
    edge = known_w10_correction_edge()
    assert edge.older_disclosure_id == "1122417"
    assert edge.newer_disclosure_id == "1126845"
    assert edge.older_published_at < edge.newer_published_at


def test_correction_edge_rejects_reverse_time() -> None:
    with pytest.raises(ValueError, match="move forward"):
        CorrectionEdge(
            older_disclosure_id="2",
            newer_disclosure_id="1",
            older_published_at=datetime(2023, 3, 2, tzinfo=UTC),
            newer_published_at=datetime(2023, 3, 1, tzinfo=UTC),
            relation_label="bad",
        )


def test_duplicate_disclosure_conflict_is_rejected() -> None:
    first = DisclosureVersionRecord(
        disclosure_id="1",
        published_at=datetime(2023, 3, 1, tzinfo=UTC),
        report_year=2022,
        report_period=4,
        stock_codes=("AAA",),
        modify_status="DUZELTILEN",
        response_sha256="a" * 64,
    )
    second = DisclosureVersionRecord(
        disclosure_id="1",
        published_at=datetime(2023, 3, 1, tzinfo=UTC),
        report_year=2022,
        report_period=4,
        stock_codes=("AAA",),
        modify_status="DUZELTILEN",
        response_sha256="b" * 64,
    )
    with pytest.raises(ValueError, match="conflicting payload"):
        validate_unique_disclosures((first, second))


def test_successful_windows_never_imply_complete_authority() -> None:
    status = classify_enumeration_status(
        windows_requested=60,
        windows_succeeded=60,
        correction_edges=19,
    )
    assert status is EnumerationStatus.ENUMERATED_WITH_CORRECTION_CHAINS
    with pytest.raises(ValueError, match="no proven completeness guarantee"):
        EnumerationReceipt(
            run_id="bad",
            captured_at=datetime(2026, 10, 5, tzinfo=UTC),
            windows_requested=60,
            windows_succeeded=60,
            windows_failed=0,
            distinct_disclosures=1000,
            correction_edges=19,
            status=status,
            completeness_guaranteed=True,
            blocker_code="NONE",
        )


def test_partial_windows_stay_partial() -> None:
    assert classify_enumeration_status(
        windows_requested=60,
        windows_succeeded=59,
        correction_edges=10,
    ) is EnumerationStatus.ENUMERATED_PARTIAL
