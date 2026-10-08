import pytest

from zincir_kiran.corporate_action_economic_resolution import (
    EconomicResolutionEvidence,
    EconomicResolutionStatus,
    ShareMultiplierContractEvidence,
    evaluate_share_multiplier_contract,
    resolve_economic_action,
)


def evidence(**overrides):
    values = {
        "event_id": "1674751",
        "event_type": "DIVIDEND_PROCESS_DISCLOSURE",
        "official_detail_captured": True,
        "official_detail_sha256": "a" * 64,
        "official_economic_fields_complete": False,
        "official_non_price_affecting_explicit": False,
        "vendor_corroboration_present": False,
        "source_conflict": False,
    }
    values.update(overrides)
    return EconomicResolutionEvidence(**values)


def test_vendor_only_can_never_release_risk():
    result = resolve_economic_action(
        evidence(vendor_corroboration_present=True)
    )
    assert result.status is EconomicResolutionStatus.VENDOR_CORROBORATED_ONLY
    assert result.risk_released is False
    assert result.shadow_signal_allowed is False


def test_complete_official_economic_fields_release_event_risk():
    result = resolve_economic_action(
        evidence(official_economic_fields_complete=True)
    )
    assert (
        result.status
        is EconomicResolutionStatus.OFFICIAL_ECONOMIC_ACTION_RESOLVED
    )
    assert result.risk_released is True


def test_explicit_non_price_affecting_official_detail_can_release():
    result = resolve_economic_action(
        evidence(official_non_price_affecting_explicit=True)
    )
    assert (
        result.status
        is EconomicResolutionStatus.OFFICIAL_NON_PRICE_AFFECTING_PROCESS_RESOLVED
    )
    assert result.risk_released is True


def test_missing_official_detail_is_unresolved_even_with_vendor():
    result = resolve_economic_action(
        evidence(
            official_detail_captured=False,
            official_detail_sha256=None,
            vendor_corroboration_present=True,
        )
    )
    assert (
        result.status
        is EconomicResolutionStatus.UNRESOLVED_OFFICIAL_DETAIL_MISSING
    )
    assert result.risk_released is False


def test_source_conflict_has_highest_precedence():
    result = resolve_economic_action(
        evidence(
            source_conflict=True,
            official_economic_fields_complete=True,
            vendor_corroboration_present=True,
        )
    )
    assert result.status is EconomicResolutionStatus.SOURCE_CONFLICT
    assert result.risk_released is False


def test_resolution_claim_requires_captured_official_detail():
    with pytest.raises(ValueError, match="captured official detail"):
        evidence(
            official_detail_captured=False,
            official_detail_sha256=None,
            official_economic_fields_complete=True,
        )


def test_captured_official_detail_without_locked_field_contract_stays_unresolved():
    result = resolve_economic_action(
        evidence(
            official_detail_captured=True,
            official_detail_sha256="b" * 64,
            official_economic_fields_complete=False,
            official_non_price_affecting_explicit=False,
            vendor_corroboration_present=False,
        )
    )
    assert (
        result.status
        is EconomicResolutionStatus.UNRESOLVED_OFFICIAL_DETAIL_INSUFFICIENT
    )
    assert result.risk_released is False


def test_vendor_corroboration_does_not_upgrade_insufficient_official_detail():
    result = resolve_economic_action(
        evidence(
            official_detail_captured=True,
            official_detail_sha256="c" * 64,
            official_economic_fields_complete=False,
            official_non_price_affecting_explicit=False,
            vendor_corroboration_present=True,
        )
    )
    assert result.status is EconomicResolutionStatus.VENDOR_CORROBORATED_ONLY
    assert result.risk_released is False
    assert result.shadow_signal_allowed is False


def test_share_multiplier_contract_accepts_final_official_multiplier():
    result = evaluate_share_multiplier_contract(
        ShareMultiplierContractEvidence(
            exact_listed_ticker_share_group_once=True,
            effective_date="2026-10-08",
            effective_date_finalized=True,
            share_multiplier=2.0,
            bonus_rate_percent=None,
        )
    )
    assert result.complete is True
    assert result.reason_codes == ()


def test_share_multiplier_contract_accepts_explicit_bonus_mechanics():
    result = evaluate_share_multiplier_contract(
        ShareMultiplierContractEvidence(
            exact_listed_ticker_share_group_once=True,
            effective_date="2026-10-08",
            effective_date_finalized=True,
            share_multiplier=None,
            bonus_rate_percent=100.0,
        )
    )
    assert result.complete is True


def test_share_multiplier_contract_rejects_proposed_date():
    result = evaluate_share_multiplier_contract(
        ShareMultiplierContractEvidence(
            exact_listed_ticker_share_group_once=True,
            effective_date="2026-10-08",
            effective_date_finalized=False,
            share_multiplier=2.0,
            bonus_rate_percent=None,
        )
    )
    assert result.complete is False
    assert "EFFECTIVE_DATE_NOT_FINALIZED" in result.reason_codes


def test_share_multiplier_contract_rejects_missing_economic_mechanics():
    result = evaluate_share_multiplier_contract(
        ShareMultiplierContractEvidence(
            exact_listed_ticker_share_group_once=True,
            effective_date="2026-10-08",
            effective_date_finalized=True,
            share_multiplier=1.0,
            bonus_rate_percent=0.0,
        )
    )
    assert result.complete is False
    assert "SHARE_MULTIPLIER_OR_BONUS_MECHANICS_MISSING" in result.reason_codes


def test_share_multiplier_contract_requires_exact_target_match():
    result = evaluate_share_multiplier_contract(
        ShareMultiplierContractEvidence(
            exact_listed_ticker_share_group_once=False,
            effective_date="2026-10-08",
            effective_date_finalized=True,
            share_multiplier=1.5,
            bonus_rate_percent=None,
        )
    )
    assert result.complete is False
    assert "TARGET_SHARE_GROUP_NOT_EXACTLY_MATCHED_ONCE" in result.reason_codes


def test_share_multiplier_contract_rejects_invalid_values():
    with pytest.raises(ValueError, match="positive"):
        ShareMultiplierContractEvidence(
            exact_listed_ticker_share_group_once=True,
            effective_date="2026-10-08",
            effective_date_finalized=True,
            share_multiplier=0.0,
            bonus_rate_percent=None,
        )
    with pytest.raises(ValueError, match="negative"):
        ShareMultiplierContractEvidence(
            exact_listed_ticker_share_group_once=True,
            effective_date="2026-10-08",
            effective_date_finalized=True,
            share_multiplier=None,
            bonus_rate_percent=-1.0,
        )
