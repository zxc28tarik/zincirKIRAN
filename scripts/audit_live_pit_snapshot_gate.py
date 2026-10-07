#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/evidence_runs/current_bist_roster_bootstrap_v1.json"
OUT = ROOT / "research/evidence_runs/live_pit_snapshot_gate_reference_audit_v1.json"

ACTIVATION_COMMIT = "1ae3ab623df58c8a22b7f943585f3d3835588e0a"
ACTIVATION_AT = "2026-10-07T22:10:15+00:00"


def main() -> int:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    artifacts = {row["artifact_id"]: row for row in payload["artifacts"]}

    roster = artifacts["current-kap-bist-roster"]
    raw_close = artifacts["current-raw-close"]
    share_basis = artifacts["current-explicit-share-basis"]

    audit = {
        "contract": "LIVE_PIT_SNAPSHOT_GATE_REFERENCE_AUDIT_V1",
        "authority": "REFERENCE_ONLY",
        "production_ready": False,
        "real_shadow_run_created": False,
        "activation_commit": ACTIVATION_COMMIT,
        "activation_at": ACTIVATION_AT,
        "source_receipt": {
            "path": str(SOURCE.relative_to(ROOT)),
            "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        },
        "reference_artifacts": [
            {
                "artifact_id": roster["artifact_id"],
                "authority": roster["authority"],
                "shadow_v1_eligible": False,
                "reason": "DISCOVERY_ONLY_NOT_FINAL_INVESTABLE_UNIVERSE_AND_PRE_ACTIVATION_REFERENCE",
            },
            {
                "artifact_id": raw_close["artifact_id"],
                "authority": raw_close["authority"],
                "shadow_v1_eligible": False,
                "reason": "CURRENT_REFERENCE_SNAPSHOT_PREDATES_PROTOCOL_ACTIVATION_AND_LACKS_45B_LIVE_TIMESTAMP_CONTRACT",
            },
            {
                "artifact_id": share_basis["artifact_id"],
                "authority": share_basis["authority"],
                "shadow_v1_eligible": False,
                "reason": "CURRENT_REFERENCE_SNAPSHOT_PREDATES_PROTOCOL_ACTIVATION_AND_IS_NOT_A_COMPLETE_REQUIRED_SHADOW_DOMAIN",
            },
        ],
        "gate_state": {
            "contract_ready": True,
            "shadow_execution_ready": False,
            "historical_backfill_allowed": False,
            "post_activation_live_snapshot_set_present": False,
            "blocking_reason": "NO_POST_ACTIVATION_LIVE_PIT_SNAPSHOT_SET",
        },
        "next_required_work": [
            "CAPTURE_POST_ACTIVATION_LIVE_UNIVERSE_SNAPSHOT",
            "CAPTURE_POST_ACTIVATION_LIVE_MARKET_SNAPSHOT",
            "LOCK_FINANCIAL_PUBLICATION_REVISION_LIVE_SNAPSHOT_PATH",
            "LOCK_CORPORATE_ACTION_LIVE_SNAPSHOT_PATH",
        ],
    }

    OUT.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
