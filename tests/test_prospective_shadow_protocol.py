from datetime import UTC, datetime, timedelta

import pytest

from zincir_kiran.prospective_shadow_protocol import (
    DomainObservation,
    ProspectiveShadowProtocol,
    ProspectiveShadowTrack,
    ShadowDomainState,
    ShadowTrackDecision,
    canonical_protocol_hash,
    evaluate_track_availability,
    validate_prospective_temporal_boundary,
)


def track(track_id="HIGH_52W_PROXIMITY"):
    return ProspectiveShadowTrack(
        track_id=track_id,
        kind="TEST",
        required_domains=("CORPORATE_ACTIONS", "MARKET_PRICES", "UNIVERSE"),
        optional_domains=("VOLUME_LIQUIDITY",),
        missing_policy="ABSTAIN",
    )


def protocol():
    tracks = tuple(sorted(
        (
            track("HIGH_52W_PROXIMITY"),
            track("EW5_COMPOSITE"),
            track("FIXED_RIDGE_5F"),
            track("TRAIN_ONLY_EVIDENCE_WEIGHTED_5F"),
        ),
        key=lambda item: item.track_id,
    ))
    return ProspectiveShadowProtocol(
        protocol_id="ZINCIR_KIRAN_PROSPECTIVE_SHADOW_V1",
        definition_version="v1",
        activation_rule="FIRST_MAIN_MERGE_COMMIT_CONTAINING_THIS_PROTOCOL",
        horizons=("H20", "H60", "H120", "H252"),
        tracks=tracks,
        historical_backfill_allowed=False,
        broker_actions_allowed=False,
        orders_allowed=False,
        production_promotion_allowed=False,
        production_thresholds_defined=False,
    )


def available(domain):
    return DomainObservation(
        domain_id=domain,
        state=ShadowDomainState.AVAILABLE,
        snapshot_id=f"snap-{domain}",
        snapshot_sha256="a" * 64,
        reason_code=None,
    )


def test_temporal_boundary_is_strictly_prospective():
    activation = datetime(2026, 10, 8, 8, tzinfo=UTC)
    with pytest.raises(ValueError, match="strictly after"):
        validate_prospective_temporal_boundary(
            activation_at=activation,
            as_of=activation,
            executed_at=activation,
        )
    with pytest.raises(ValueError, match="strictly after"):
        validate_prospective_temporal_boundary(
            activation_at=activation,
            as_of=activation - timedelta(seconds=1),
            executed_at=activation,
        )
    validate_prospective_temporal_boundary(
        activation_at=activation,
        as_of=activation + timedelta(seconds=1),
        executed_at=activation + timedelta(seconds=2),
    )


def test_blocked_required_domain_forces_data_blocked():
    decision, reasons = evaluate_track_availability(
        track(),
        [
            available("MARKET_PRICES"),
            available("UNIVERSE"),
            DomainObservation(
                domain_id="CORPORATE_ACTIONS",
                state=ShadowDomainState.BLOCKED,
                snapshot_id=None,
                snapshot_sha256=None,
                reason_code="AUTHORITY_BLOCKED",
            ),
        ],
    )
    assert decision is ShadowTrackDecision.DATA_BLOCKED
    assert reasons == ("BLOCKED_DOMAIN:CORPORATE_ACTIONS:AUTHORITY_BLOCKED",)


def test_missing_required_domain_never_neutral_fills():
    decision, reasons = evaluate_track_availability(
        track(),
        [available("MARKET_PRICES"), available("UNIVERSE")],
    )
    assert decision is ShadowTrackDecision.FACTOR_UNAVAILABLE
    assert reasons == ("MISSING_DOMAIN:CORPORATE_ACTIONS",)


def test_all_required_domains_can_be_signal_eligible():
    decision, reasons = evaluate_track_availability(
        track(),
        [
            available("CORPORATE_ACTIONS"),
            available("MARKET_PRICES"),
            available("UNIVERSE"),
        ],
    )
    assert decision is ShadowTrackDecision.SIGNAL_ELIGIBLE
    assert reasons == ()


def test_protocol_forbids_backfill_orders_promotion_and_thresholds():
    p = protocol()
    assert p.historical_backfill_allowed is False
    assert p.orders_allowed is False
    assert p.broker_actions_allowed is False
    assert p.production_promotion_allowed is False
    assert p.production_thresholds_defined is False


def test_protocol_hash_is_deterministic():
    assert canonical_protocol_hash(protocol()) == canonical_protocol_hash(protocol())
    assert len(canonical_protocol_hash(protocol())) == 64
