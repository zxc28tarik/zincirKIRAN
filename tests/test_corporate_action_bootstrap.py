from datetime import UTC, datetime

import pytest

from zincir_kiran.corporate_action_bootstrap import (
    BootstrapAuthority,
    BootstrapEventType,
    CorporateActionEvidence,
    CoveredInventoryWindow,
    classify_share_count_subject,
    production_action_type,
    require_absence_authority,
    require_official_ticker_change,
)
from zincir_kiran.corporate_actions import CorporateActionType


def test_subject_classifier_maps_supported_markers() -> None:
    assert classify_share_count_subject("Sermaye Artırımı") is BootstrapEventType.CAPITAL_INCREASE
    assert classify_share_count_subject("Sermaye Azaltımı") is BootstrapEventType.CAPITAL_DECREASE
    assert classify_share_count_subject("Birleşme İşlemleri") is BootstrapEventType.MERGER
    assert classify_share_count_subject("Bölünme İşlemleri") is BootstrapEventType.DEMERGER
    assert classify_share_count_subject("Pay Grubu Değişikliği") is BootstrapEventType.SHARE_CLASS_CHANGE


def test_classifier_is_fail_closed_for_multiple_markers() -> None:
    subject = "Sermaye artırımı ve birleşme hakkında"
    assert classify_share_count_subject(subject) is BootstrapEventType.AMBIGUOUS_SHARE_COUNT_ACTION


def test_unrelated_subject_is_not_fabricated_as_action() -> None:
    assert classify_share_count_subject("Faaliyet Raporu") is None


def test_only_semantically_exact_events_map_to_production_taxonomy() -> None:
    assert production_action_type(BootstrapEventType.MERGER) is CorporateActionType.MERGER
    assert production_action_type(BootstrapEventType.DEMERGER) is CorporateActionType.DEMERGER
    assert production_action_type(BootstrapEventType.CAPITAL_INCREASE) is None


def test_absence_requires_complete_inventory_window() -> None:
    incomplete = CoveredInventoryWindow(
        start_at=datetime(2023, 1, 1, tzinfo=UTC),
        end_at=datetime(2023, 1, 31, tzinfo=UTC),
        complete=False,
        source_manifest_sha256="a" * 64,
    )
    with pytest.raises(ValueError, match="complete covered window"):
        require_absence_authority(incomplete)


def test_ticker_change_requires_official_borsa_authority() -> None:
    event = CorporateActionEvidence(
        event_id="x",
        published_at=datetime(2024, 10, 1, tzinfo=UTC),
        ticker="GRTHO",
        subject="Ticker change",
        event_type=BootstrapEventType.TICKER_CHANGE,
        authority=BootstrapAuthority.POSITIVE_EVENT_EVIDENCE,
        source_sha256="b" * 64,
        source_system="KAP",
    )
    with pytest.raises(ValueError, match="official Borsa lineage"):
        require_official_ticker_change(event)


def test_real_kap_bonus_issue_examples_are_classified() -> None:
    assert classify_share_count_subject(
        "Sermaye Artırımı - Azaltımı İşlemlerine İlişkin Bildirim",
        "İç Kaynaklardan Bedelsiz Sermaye Artırımı",
    ) is BootstrapEventType.BONUS_ISSUE_DISCLOSURE
    assert classify_share_count_subject(
        "Sermaye Artırımı - Azaltımı İşlemlerine İlişkin Bildirim",
        "Bedelsiz Sermaye Artırımına İlişkin SPK Başvurusu",
    ) is BootstrapEventType.BONUS_ISSUE_DISCLOSURE


def test_real_kap_rights_issue_example_is_classified() -> None:
    assert classify_share_count_subject(
        "Sermaye Artırımından Elde Edilecek - Edilen Fonun Kullanımına İlişkin Rapor",
        "Bedelli Sermaye Arttırımından Elde Edilecek Fonun Kullanımına İlişkin Rapor",
    ) is BootstrapEventType.RIGHTS_ISSUE_DISCLOSURE


def test_real_kap_dividend_process_example_is_not_cash_amount_claim() -> None:
    event_type = classify_share_count_subject(
        "Kar Payı Dağıtım İşlemlerine İlişkin Bildirim",
        "2022 yılı Kar Payı Dağıtımına İlişkin Genel Kurul Kararı",
    )
    assert event_type is BootstrapEventType.DIVIDEND_PROCESS_DISCLOSURE
    assert production_action_type(event_type) is None


def test_bonus_and_rights_subtypes_map_only_to_category_not_ratio() -> None:
    assert production_action_type(
        BootstrapEventType.BONUS_ISSUE_DISCLOSURE
    ) is CorporateActionType.BONUS_ISSUE
    assert production_action_type(
        BootstrapEventType.RIGHTS_ISSUE_DISCLOSURE
    ) is CorporateActionType.RIGHTS_ISSUE
