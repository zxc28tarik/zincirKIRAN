from datetime import UTC, datetime, timedelta

import pytest

from zincir_kiran.baselines import Horizon
from zincir_kiran.shadow import (
    ShadowDecision,
    ShadowProtocol,
    ShadowSecurityDecision,
    attach_realized_label,
    build_shadow_run,
    verify_shadow_replay,
)


PREREGISTERED = datetime(2026, 10, 1, tzinfo=UTC)
AS_OF = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)
EXECUTED = datetime(2026, 10, 4, 7, 1, tzinfo=UTC)


def protocol() -> ShadowProtocol:
    return ShadowProtocol(
        protocol_id="shadow-v1",
        definition_version="v1",
        universe_rule_version="universe-v1",
        alpha_specification_id="alpha-h20",
        alpha_definition_version="v1",
        confidence_specification_id="confidence-h20",
        confidence_definition_version="v1",
        ml_challenger_id="ridge-h20-v1",
        ml_definition_version="v1",
        preregistered_at=PREREGISTERED,
        horizons=(Horizon.H20, Horizon.H60),
    )


def decisions() -> list[ShadowSecurityDecision]:
    return [
        ShadowSecurityDecision(
            security_id="BBB",
            decision=ShadowDecision.NO_SIGNAL,
            alpha_score=0.1,
            confidence_score=0.2,
            ml_score=-0.1,
            portfolio_target_weight=None,
            reason_codes=("LOW_CONFIDENCE",),
        ),
        ShadowSecurityDecision(
            security_id="AAA",
            decision=ShadowDecision.SIGNAL_ELIGIBLE,
            alpha_score=0.8,
            confidence_score=0.9,
            ml_score=0.7,
            portfolio_target_weight=0.05,
            reason_codes=(),
        ),
    ]


def run():
    return build_shadow_run(
        protocol=protocol(),
        shadow_run_id="shadow-run-1",
        as_of=AS_OF,
        executed_at=EXECUTED,
        data_snapshot_id="data-snapshot-1",
        universe_snapshot_id="universe-snapshot-1",
        input_provenance={
            "alpha_run_id": "alpha-1",
            "confidence_run_id": "confidence-1",
            "ml_fit_id": "ml-fit-1",
        },
        decisions=decisions(),
    )


def test_shadow_run_is_deterministic_and_security_sorted() -> None:
    first = run()
    second = build_shadow_run(
        protocol=protocol(),
        shadow_run_id="shadow-run-1",
        as_of=AS_OF,
        executed_at=EXECUTED,
        data_snapshot_id="data-snapshot-1",
        universe_snapshot_id="universe-snapshot-1",
        input_provenance={
            "ml_fit_id": "ml-fit-1",
            "confidence_run_id": "confidence-1",
            "alpha_run_id": "alpha-1",
        },
        decisions=list(reversed(decisions())),
    )
    assert first.input_receipt_hash == second.input_receipt_hash
    assert first.output_receipt_hash == second.output_receipt_hash
    assert tuple(item.security_id for item in first.decisions) == ("AAA", "BBB")


def test_shadow_run_cannot_predate_preregistration() -> None:
    with pytest.raises(ValueError, match="predate"):
        build_shadow_run(
            protocol=protocol(),
            shadow_run_id="bad",
            as_of=datetime(2026, 9, 30, tzinfo=UTC),
            executed_at=EXECUTED,
            data_snapshot_id="data",
            universe_snapshot_id="universe",
            input_provenance={"alpha_run_id": "a"},
            decisions=[],
        )


def test_no_signal_cannot_hide_portfolio_intent() -> None:
    with pytest.raises(ValueError, match="portfolio intent"):
        ShadowSecurityDecision(
            security_id="AAA",
            decision=ShadowDecision.NO_SIGNAL,
            alpha_score=0.2,
            confidence_score=0.1,
            ml_score=None,
            portfolio_target_weight=0.05,
            reason_codes=("LOW_CONFIDENCE",),
        )


def test_replay_detects_changed_output() -> None:
    stored = run()
    changed = build_shadow_run(
        protocol=protocol(),
        shadow_run_id="shadow-run-2",
        as_of=AS_OF,
        executed_at=EXECUTED,
        data_snapshot_id="data-snapshot-1",
        universe_snapshot_id="universe-snapshot-1",
        input_provenance={
            "alpha_run_id": "alpha-1",
            "confidence_run_id": "confidence-1",
            "ml_fit_id": "ml-fit-1",
        },
        decisions=[
            ShadowSecurityDecision(
                security_id="AAA",
                decision=ShadowDecision.SIGNAL_ELIGIBLE,
                alpha_score=0.81,
                confidence_score=0.9,
                ml_score=0.7,
                portfolio_target_weight=0.05,
                reason_codes=(),
            ),
            decisions()[0],
        ],
    )
    with pytest.raises(ValueError, match="output receipt"):
        verify_shadow_replay(stored, changed)


def test_realized_label_cannot_arrive_before_horizon_matures() -> None:
    stored = run()
    with pytest.raises(ValueError, match="premature"):
        attach_realized_label(
            run=stored,
            security_id="AAA",
            horizon=Horizon.H20,
            label_available_at=AS_OF + timedelta(days=10),
            market_relative_total_return=0.04,
        )


def test_realized_label_can_be_attached_after_explicit_maturity() -> None:
    stored = run()
    label = attach_realized_label(
        run=stored,
        security_id="AAA",
        horizon=Horizon.H20,
        label_available_at=AS_OF + timedelta(days=20),
        market_relative_total_return=0.04,
    )
    assert label.horizon is Horizon.H20
    assert label.market_relative_total_return == pytest.approx(0.04)


def test_realized_label_security_must_have_been_in_shadow_universe() -> None:
    with pytest.raises(ValueError, match="not present"):
        attach_realized_label(
            run=run(),
            security_id="ZZZ",
            horizon=Horizon.H20,
            label_available_at=AS_OF + timedelta(days=20),
            market_relative_total_return=0.01,
        )
