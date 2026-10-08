from zincir_kiran.corporate_action_detail_stage import (
    OfficialDetailStage,
    OfficialDetailStageEvidence,
    classify_official_detail_stage,
)


def classify(title, summary=None, event_type="CAPITAL_INCREASE"):
    return classify_official_detail_stage(
        OfficialDetailStageEvidence(
            event_id="1",
            event_type=event_type,
            title=title,
            summary=summary,
        )
    )


def test_draft_prospectus_is_process_only():
    result = classify(
        "İzahname (SPK Onayına Sunulan)",
        "Bedelli ve Bedelsiz Sermaye Artırımına İlişkin SPK Onayına Sunulan Taslak İzahname",
    )
    assert result.stage is OfficialDetailStage.PROCESS_ONLY
    assert result.risk_released is False


def test_fund_use_report_is_process_only():
    result = classify(
        "Sermaye Artırımından Elde Edilecek / Edilen Fonun Kullanımına İlişkin Rapor"
    )
    assert result.stage is OfficialDetailStage.PROCESS_ONLY


def test_dividend_distribution_form_is_economic_candidate_not_resolved():
    result = classify(
        "Kar Payı Dağıtım İşlemlerine İlişkin Bildirim",
        event_type="DIVIDEND_PROCESS_DISCLOSURE",
    )
    assert result.stage is OfficialDetailStage.ECONOMIC_DETAIL_CANDIDATE
    assert result.risk_released is False


def test_unknown_title_stays_unknown():
    result = classify("Özel Durum Açıklaması")
    assert result.stage is OfficialDetailStage.UNKNOWN
    assert result.risk_released is False
