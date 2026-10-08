import pytest

from zincir_kiran.corporate_action_economic_resolution import (
    EconomicResolutionEvidence,
    EconomicResolutionStatus,
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
