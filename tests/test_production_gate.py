from datetime import UTC, datetime

import pytest

from zincir_kiran.production_gate import (
    ProductionDecision,
    ProductionEvidence,
    ProductionGateSpec,
    evaluate_production_gate,
)

PREREGISTERED = datetime(2026, 10, 4, 9, 0, tzinfo=UTC)
EVALUATED = datetime(2026, 12, 31, 9, 0, tzinfo=UTC)


def spec() -> ProductionGateSpec:
    return ProductionGateSpec(
        gate_id="prod-gate-v1",
        definition_version="v1",
        preregistered_at=PREREGISTERED,
        minimum_shadow_days=60,
        minimum_shadow_runs=40,
        minimum_realized_label_coverage=0.80,
        minimum_mean_ic=0.02,
        minimum_net_return_after_costs=0.01,
        maximum_drawdown=0.25,
        minimum_liquidity_fit=0.70,
    )


def evidence(**overrides: object) -> ProductionEvidence:
    values: dict[str, object] = {
        "evaluated_at": EVALUATED,
        "tournament_run_id": "tournament-run-1",
        "shadow_protocol_id": "shadow-v1",
        "shadow_days": 90,
        "shadow_runs": 65,
        "realized_label_coverage": 0.90,
        "mean_ic": 0.04,
        "net_return_after_costs": 0.03,
        "max_drawdown": 0.18,
        "liquidity_fit": 0.90,
        "replay_integrity": True,
        "pit_integrity": True,
        "cost_model_present": True,
        "capacity_evidence_present": True,
    }
    values.update(overrides)
    return ProductionEvidence(**values)  # type: ignore[arg-type]


def test_missing_required_evidence_fails_closed_to_research_only() -> None:
    outcome = evaluate_production_gate(spec(), evidence(mean_ic=None))
    assert outcome.decision is ProductionDecision.RESEARCH_ONLY
    assert "mean_ic" in outcome.missing_evidence
    assert outcome.automatic_deployment is False


def test_insufficient_shadow_evidence_extends_shadow() -> None:
    outcome = evaluate_production_gate(spec(), evidence(shadow_days=30))
    assert outcome.decision is ProductionDecision.EXTEND_SHADOW
    assert outcome.failed_checks == ("minimum_shadow_days",)


def test_integrity_failure_rejects() -> None:
    outcome = evaluate_production_gate(spec(), evidence(replay_integrity=False))
    assert outcome.decision is ProductionDecision.REJECTED
    assert outcome.failed_checks == ("replay_integrity",)


def test_performance_or_liquidity_failure_rejects() -> None:
    outcome = evaluate_production_gate(
        spec(),
        evidence(mean_ic=0.0, liquidity_fit=0.5),
    )
    assert outcome.decision is ProductionDecision.REJECTED
    assert outcome.failed_checks == ("minimum_liquidity_fit", "minimum_mean_ic")


def test_all_checks_pass_only_to_manual_review_eligibility() -> None:
    outcome = evaluate_production_gate(spec(), evidence())
    assert outcome.decision is ProductionDecision.PRODUCTION_ELIGIBLE_REVIEW_REQUIRED
    assert outcome.review_required is True
    assert outcome.automatic_deployment is False
    assert outcome.failed_checks == ()
    assert outcome.missing_evidence == ()


def test_evaluation_must_follow_preregistration() -> None:
    with pytest.raises(ValueError, match="follow preregistration"):
        evaluate_production_gate(
            spec(),
            evidence(evaluated_at=PREREGISTERED),
        )


def test_invalid_thresholds_are_rejected() -> None:
    with pytest.raises(ValueError, match="minimum_realized_label_coverage"):
        ProductionGateSpec(
            gate_id="bad",
            definition_version="v1",
            preregistered_at=PREREGISTERED,
            minimum_shadow_days=0,
            minimum_shadow_runs=0,
            minimum_realized_label_coverage=1.1,
            minimum_mean_ic=0.0,
            minimum_net_return_after_costs=0.0,
            maximum_drawdown=0.5,
            minimum_liquidity_fit=0.5,
        )
