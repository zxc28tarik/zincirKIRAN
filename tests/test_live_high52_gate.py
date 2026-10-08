import pytest

from zincir_kiran.live_high52_gate import (
    High52InputEvidence,
    High52InputStatus,
    evaluate_high52_input,
)


def evidence(**overrides):
    values = {
        "ticker": "AEFES",
        "adj_close_observations": 300,
        "finite_positive_adj_close_observations": 300,
        "recent_ca_coverage_complete": True,
        "unresolved_recent_ca_event_ids": (),
        "historical_ca_lookback_reconciled": True,
    }
    values.update(overrides)
    return High52InputEvidence(**values)


def test_requires_at_least_252_finite_positive_adj_close_observations():
    result = evaluate_high52_input(
        evidence(
            adj_close_observations=251,
            finite_positive_adj_close_observations=251,
        )
    )
    assert result.status is High52InputStatus.PRICE_HISTORY_INSUFFICIENT
    assert result.score_computation_allowed is False
    assert result.shadow_signal_allowed is False


def test_incomplete_recent_ca_gap_blocks_score():
    result = evaluate_high52_input(
        evidence(recent_ca_coverage_complete=False)
    )
    assert result.status is High52InputStatus.CA_COVERAGE_INCOMPLETE
    assert result.score_computation_allowed is False


def test_unresolved_recent_ca_event_blocks_score():
    result = evaluate_high52_input(
        evidence(unresolved_recent_ca_event_ids=("kap-123",))
    )
    assert result.status is High52InputStatus.RECENT_CA_RISK_UNRESOLVED
    assert "UNRESOLVED_RECENT_CA:kap-123" in result.reason_codes


def test_historical_ca_reconciliation_is_separate_required_gate():
    result = evaluate_high52_input(
        evidence(historical_ca_lookback_reconciled=False)
    )
    assert (
        result.status
        is High52InputStatus.HISTORICAL_CA_RECONCILIATION_REQUIRED
    )
    assert result.score_computation_allowed is False


def test_ready_inputs_still_cannot_emit_shadow_signal_in_45d():
    result = evaluate_high52_input(evidence())
    assert result.status is High52InputStatus.READY
    assert result.score_computation_allowed is True
    assert result.shadow_signal_allowed is False


def test_unresolved_event_ids_must_be_sorted_unique():
    with pytest.raises(ValueError, match="unique and sorted"):
        evidence(unresolved_recent_ca_event_ids=("b", "a"))
