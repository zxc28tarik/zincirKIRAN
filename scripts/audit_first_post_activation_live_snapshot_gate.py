#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from zincir_kiran.live_shadow_snapshot import (
    LiveSnapshotArtifact,
    LiveSnapshotAuthority,
    evaluate_shadow_execution_gate,
)
from zincir_kiran.prospective_shadow_protocol import ProspectiveShadowTrack

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/live_shadow/first_post_activation_live_snapshot_v1"
PROTOCOL = ROOT / "research/preregistrations/prospective_shadow_protocol_v1.json"
ACTIVATION = datetime.fromisoformat("2026-10-07T22:10:15+00:00")
UNIVERSE_AVAILABLE = datetime.fromisoformat("2026-10-01T00:00:00+03:00")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    provenance = json.loads((OUT / "provenance.json").read_text(encoding="utf-8"))
    captured_at = datetime.fromisoformat(provenance["captured_at"])
    if captured_at <= ACTIVATION:
        raise RuntimeError("captured snapshot is not prospective")

    universe_path = OUT / "universe.csv"
    market_path = OUT / "market.csv.gz"

    snapshots = [
        LiveSnapshotArtifact(
            snapshot_id="live-universe-v1",
            domain_id="UNIVERSE",
            source_id="borsa_istanbul_plus_frozen_q3_anchor",
            source_url=provenance["universe"]["official_q4_source_url"],
            logical_key="shadow-v1:UNIVERSE",
            source_available_at=UNIVERSE_AVAILABLE,
            captured_at=captured_at,
            retrieved_at=captured_at,
            content_sha256=sha(universe_path),
            byte_size=universe_path.stat().st_size,
            authority=LiveSnapshotAuthority.VALIDATED_LIVE_RESEARCH,
        ),
        LiveSnapshotArtifact(
            snapshot_id="live-market-prices-v1",
            domain_id="MARKET_PRICES",
            source_id="yahoo_finance",
            source_url="https://finance.yahoo.com/",
            logical_key="shadow-v1:MARKET_PRICES",
            source_available_at=captured_at,
            captured_at=captured_at,
            retrieved_at=captured_at,
            content_sha256=sha(market_path),
            byte_size=market_path.stat().st_size,
            authority=LiveSnapshotAuthority.VALIDATED_LIVE_RESEARCH,
        ),
        LiveSnapshotArtifact(
            snapshot_id="live-volume-liquidity-v1",
            domain_id="VOLUME_LIQUIDITY",
            source_id="yahoo_finance",
            source_url="https://finance.yahoo.com/",
            logical_key="shadow-v1:VOLUME_LIQUIDITY",
            source_available_at=captured_at,
            captured_at=captured_at,
            retrieved_at=captured_at,
            content_sha256=sha(market_path),
            byte_size=market_path.stat().st_size,
            authority=LiveSnapshotAuthority.VALIDATED_LIVE_RESEARCH,
        ),
    ]

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    results = {}
    for row in protocol["tracks"]:
        track = ProspectiveShadowTrack(
            track_id=row["track_id"],
            kind=row["kind"],
            required_domains=tuple(sorted(row["required_domains"])),
            optional_domains=tuple(sorted(row["optional_domains"])),
            missing_policy=row["missing_policy"],
        )
        result = evaluate_shadow_execution_gate(
            track=track,
            activation_at=ACTIVATION,
            as_of=captured_at,
            executed_at=captured_at,
            snapshots=snapshots,
        )
        results[track.track_id] = {
            "decision": result.decision.value,
            "reasons": result.reasons,
            "eligible_snapshot_ids": result.eligible_snapshot_ids,
            "manifest_sha256": result.manifest_sha256,
        }

    if any(row["decision"] == "SIGNAL_ELIGIBLE" for row in results.values()):
        raise RuntimeError(
            "45C must not make any track signal-eligible before missing live domains are locked"
        )

    audit = {
        "contract": "FIRST_POST_ACTIVATION_LIVE_SNAPSHOT_GATE_AUDIT_V1",
        "captured_at": captured_at.isoformat(),
        "activation_at": ACTIVATION.isoformat(),
        "real_shadow_run_created": False,
        "available_domains": [
            "UNIVERSE",
            "MARKET_PRICES",
            "VOLUME_LIQUIDITY",
        ],
        "track_results": results,
        "shadow_execution_ready": False,
        "blocking_state": "REQUIRED_LIVE_DOMAINS_STILL_MISSING",
    }
    path = OUT / "gate_audit.json"
    path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    sums_path = OUT / "SHA256SUMS"
    rows = {}
    if sums_path.exists():
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            rows[name] = digest
    rows[path.name] = sha(path)
    sums_path.write_text(
        "\n".join(f"{rows[name]}  {name}" for name in sorted(rows)) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
