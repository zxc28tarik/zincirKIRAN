import pytest

from zincir_kiran.live_high52_reconciliation import (
    High52ReconciledStatus,
    High52ReconciliationEvidence,
    evaluate_high52_reconciliation,
)


def evidence(**overrides):
    values = {
        "ticker": "AEFES",
        "finite_positive_adj_close_observations": 300,
        "historical_ca_coverage_complete": True,
        "unresolved_historical_ca_event_ids": (),
        "unresolved_recent_ca_event_ids": (),
    }
    values.update(overrides)
    return High52ReconciliationEvidence(**values)


def test_price_history_failure_has_highest_precedence():
    result = evaluate_high52_reconciliation(
        evidence(
            finite_positive_adj_close_observations=224,
            unresolved_historical_ca_event_ids=("1",),
        )
    )
    assert result.status is High52ReconciledStatus.PRICE_HISTORY_INSUFFICIENT
    assert result.factor_input_ready is False


def test_historical_coverage_failure_is_fail_closed():
    result = evaluate_high52_reconciliation(
        evidence(historical_ca_coverage_complete=False)
    )
    assert (
        result.status
        is High52ReconciledStatus.HISTORICAL_CA_COVERAGE_INCOMPLETE
    )


def test_historical_risk_precedes_recent_risk():
    result = evaluate_high52_reconciliation(
        evidence(
            unresolved_historical_ca_event_ids=("100",),
            unresolved_recent_ca_event_ids=("200",),
        )
    )
    assert result.status is High52ReconciledStatus.HISTORICAL_CA_RISK_UNRESOLVED
    assert "UNRESOLVED_HISTORICAL_CA:100" in result.reason_codes


def test_recent_risk_blocks_otherwise_ready_input():
    result = evaluate_high52_reconciliation(
        evidence(unresolved_recent_ca_event_ids=("200",))
    )
    assert result.status is High52ReconciledStatus.RECENT_CA_RISK_UNRESOLVED
    assert result.score_computation_allowed is False


def test_clean_reconciled_ticker_can_be_factor_input_ready_but_no_shadow_signal():
    result = evaluate_high52_reconciliation(evidence())
    assert result.status is High52ReconciledStatus.FACTOR_INPUT_READY
    assert result.factor_input_ready is True
    assert result.score_computation_allowed is True
    assert result.shadow_signal_allowed is False


def test_event_ids_must_be_sorted_unique():
    with pytest.raises(ValueError, match="unique and sorted"):
        evidence(unresolved_historical_ca_event_ids=("b", "a"))
