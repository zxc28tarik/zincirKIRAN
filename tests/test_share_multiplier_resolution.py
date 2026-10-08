from zincir_kiran.share_multiplier_resolution import (
    extract_share_multiplier_contract,
)


def cells(*rows):
    out = []
    for row_index, values in enumerate(rows):
        for cell_index, value in enumerate(values):
            out.append(
                {
                    "table_index": 0,
                    "row_index": row_index,
                    "cell_index": cell_index,
                    "cell_text": value,
                }
            )
    return out


def test_explicit_bonus_contract_extracts_complete_evidence():
    result = extract_share_multiplier_contract(
        cells(
            ["Pay Grup Bilgileri", "ABC pay grubu Borsa ABC"],
            ["Bedelsiz Pay Alma Oranı (%)", "100,0000"],
            ["Bedelsiz Pay Alma Hakkı Kullanım Tarihi", "08.10.2026"],
        ),
        ticker="ABC",
    )
    assert result.contract.complete is True
    assert result.evidence.effective_date == "2026-10-08"
    assert result.evidence.effective_date_finalized is True
    assert result.evidence.bonus_rate_percent == 100.0
    assert result.matched_target_rows == 1


def test_proposed_effective_date_does_not_resolve():
    result = extract_share_multiplier_contract(
        cells(
            ["Pay Grup Bilgileri", "ABC pay grubu Borsa ABC"],
            ["Bedelsiz Pay Alma Oranı (%)", "50"],
            ["Öngörülen Hak Kullanım Tarihi", "08.10.2026"],
        ),
        ticker="ABC",
    )
    assert result.contract.complete is False
    assert result.evidence.effective_date is None
    assert "ONLY_PROVISIONAL_EFFECTIVE_DATE_FOUND" in result.extraction_reason_codes


def test_capital_amounts_are_not_inferred_into_bonus_rate():
    result = extract_share_multiplier_contract(
        cells(
            ["Pay Grup Bilgileri", "ABC pay grubu Borsa ABC"],
            ["Mevcut Sermaye", "1000000"],
            ["Ulaşılacak Sermaye", "2000000"],
            ["Hak Kullanım Tarihi", "08.10.2026"],
        ),
        ticker="ABC",
    )
    assert result.contract.complete is False
    assert result.evidence.bonus_rate_percent is None
    assert "POSITIVE_BONUS_RATE_NOT_FOUND" in result.extraction_reason_codes


def test_multiple_target_rows_fail_closed():
    result = extract_share_multiplier_contract(
        cells(
            ["Pay Grup Bilgileri", "ABC pay grubu Borsa ABC"],
            ["Pay Grup Bilgileri", "ABC ikinci pay grubu Borsa ABC"],
            ["Bedelsiz Pay Alma Oranı (%)", "100"],
            ["Hak Kullanım Tarihi", "08.10.2026"],
        ),
        ticker="ABC",
    )
    assert result.contract.complete is False
    assert "AMBIGUOUS_TARGET_SHARE_GROUP" in result.extraction_reason_codes


def test_conflicting_final_dates_fail_closed():
    result = extract_share_multiplier_contract(
        cells(
            ["Pay Grup Bilgileri", "ABC pay grubu Borsa ABC"],
            ["Bedelsiz Pay Alma Oranı (%)", "100"],
            ["Hak Kullanım Tarihi", "08.10.2026"],
            ["Hak Kullanım Tarihi", "09.10.2026"],
        ),
        ticker="ABC",
    )
    assert result.contract.complete is False
    assert "AMBIGUOUS_EFFECTIVE_DATE" in result.extraction_reason_codes


def test_conflicting_bonus_rates_fail_closed():
    result = extract_share_multiplier_contract(
        cells(
            ["Pay Grup Bilgileri", "ABC pay grubu Borsa ABC"],
            ["Bedelsiz Pay Alma Oranı (%)", "100"],
            ["Bedelsiz Pay Alma Oranı (%)", "150"],
            ["Hak Kullanım Tarihi", "08.10.2026"],
        ),
        ticker="ABC",
    )
    assert result.contract.complete is False
    assert "AMBIGUOUS_BONUS_RATE" in result.extraction_reason_codes
