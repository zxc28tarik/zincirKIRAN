from datetime import UTC, datetime, timedelta

import pytest

from zincir_kiran.live_shadow_snapshot import (
    LiveSnapshotArtifact,
    LiveSnapshotAuthority,
    evaluate_shadow_execution_gate,
    reject_conflicting_live_snapshots,
)
from zincir_kiran.prospective_shadow_protocol import (
    ProspectiveShadowTrack,
    ShadowTrackDecision,
)

ACTIVATION = datetime(2026, 10, 7, 22, 10, 15, tzinfo=UTC)
AS_OF = ACTIVATION + timedelta(hours=10)
EXECUTED = AS_OF + timedelta(minutes=2)


def track():
    return ProspectiveShadowTrack(
        track_id="HIGH_52W_PROXIMITY",
        kind="INTERPRETABLE_SINGLE_FACTOR",
        required_domains=("CORPORATE_ACTIONS", "MARKET_PRICES", "UNIVERSE"),
        optional_domains=("VOLUME_LIQUIDITY",),
        missing_policy="ABSTAIN",
    )


def snap(
    domain,
    *,
    snapshot_id=None,
    captured_at=None,
    authority=LiveSnapshotAuthority.AUTHORITATIVE_LIVE,
    digest="a" * 64,
    logical_key=None,
):
    captured = captured_at or (ACTIVATION + timedelta(hours=1))
    return LiveSnapshotArtifact(
        snapshot_id=snapshot_id or f"snap-{domain}",
        domain_id=domain,
        source_id="source",
        source_url="https://example.invalid/source",
        logical_key=logical_key or f"live:{domain}",
        source_available_at=captured - timedelta(minutes=1),
        captured_at=captured,
        retrieved_at=captured + timedelta(minutes=1),
        content_sha256=digest,
        byte_size=10,
        authority=authority,
    )


def all_required():
    return [
        snap("CORPORATE_ACTIONS"),
        snap("MARKET_PRICES"),
        snap("UNIVERSE"),
    ]


def test_all_post_activation_authorized_snapshots_can_pass_gate():
    result = evaluate_shadow_execution_gate(
        track=track(),
        activation_at=ACTIVATION,
        as_of=AS_OF,
        executed_at=EXECUTED,
        snapshots=all_required(),
    )
    assert result.decision is ShadowTrackDecision.SIGNAL_ELIGIBLE
    assert len(result.eligible_snapshot_ids) == 3
    assert len(result.manifest_sha256) == 64


def test_pre_activation_snapshot_is_blocked_not_backfilled():
    result = evaluate_shadow_execution_gate(
        track=track(),
        activation_at=ACTIVATION,
        as_of=AS_OF,
        executed_at=EXECUTED,
        snapshots=[
            snap(
                "MARKET_PRICES",
                captured_at=ACTIVATION - timedelta(seconds=1),
            ),
            snap("CORPORATE_ACTIONS"),
            snap("UNIVERSE"),
        ],
    )
    assert result.decision is ShadowTrackDecision.DATA_BLOCKED
    assert any("TEMPORAL_AUTHORITY_FAILED" in reason for reason in result.reasons)


def test_discovery_only_required_snapshot_is_blocked():
    result = evaluate_shadow_execution_gate(
        track=track(),
        activation_at=ACTIVATION,
        as_of=AS_OF,
        executed_at=EXECUTED,
        snapshots=[
            snap(
                "UNIVERSE",
                authority=LiveSnapshotAuthority.DISCOVERY_ONLY,
            ),
            snap("MARKET_PRICES"),
            snap("CORPORATE_ACTIONS"),
        ],
    )
    assert result.decision is ShadowTrackDecision.DATA_BLOCKED
    assert "BLOCKED_DOMAIN:UNIVERSE:AUTHORITY:DISCOVERY_ONLY" in result.reasons


def test_missing_required_snapshot_is_factor_unavailable():
    result = evaluate_shadow_execution_gate(
        track=track(),
        activation_at=ACTIVATION,
        as_of=AS_OF,
        executed_at=EXECUTED,
        snapshots=[snap("MARKET_PRICES"), snap("UNIVERSE")],
    )
    assert result.decision is ShadowTrackDecision.FACTOR_UNAVAILABLE
    assert "UNAVAILABLE_DOMAIN:CORPORATE_ACTIONS:NO_LIVE_SNAPSHOT" in result.reasons


def test_snapshot_after_shadow_as_of_is_blocked():
    result = evaluate_shadow_execution_gate(
        track=track(),
        activation_at=ACTIVATION,
        as_of=AS_OF,
        executed_at=EXECUTED,
        snapshots=[
            snap(
                "MARKET_PRICES",
                captured_at=AS_OF + timedelta(seconds=1),
            ),
            snap("UNIVERSE"),
            snap("CORPORATE_ACTIONS"),
        ],
    )
    assert result.decision is ShadowTrackDecision.DATA_BLOCKED


def test_conflicting_same_logical_key_hashes_rejected():
    with pytest.raises(ValueError, match="conflicting live snapshot"):
        reject_conflicting_live_snapshots(
            [
                snap(
                    "MARKET_PRICES",
                    snapshot_id="a",
                    digest="a" * 64,
                    logical_key="live:market",
                ),
                snap(
                    "MARKET_PRICES",
                    snapshot_id="b",
                    digest="b" * 64,
                    logical_key="live:market",
                ),
            ]
        )


def test_snapshot_timestamp_invariants_are_strict():
    captured = ACTIVATION + timedelta(hours=1)
    with pytest.raises(ValueError, match="source_available_at"):
        LiveSnapshotArtifact(
            snapshot_id="bad",
            domain_id="MARKET_PRICES",
            source_id="s",
            source_url="https://example.invalid",
            logical_key="bad",
            source_available_at=captured + timedelta(seconds=1),
            captured_at=captured,
            retrieved_at=captured + timedelta(seconds=2),
            content_sha256="a" * 64,
            byte_size=1,
            authority=LiveSnapshotAuthority.AUTHORITATIVE_LIVE,
        )
