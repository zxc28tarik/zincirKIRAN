#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/live_shadow/first_post_activation_live_snapshot_v1"
ACTIVATION = "2026-10-07T22:10:15+00:00"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    required = [
        "official_q4_announcement.html.gz",
        "universe.csv",
        "market.csv.gz",
        "rejections.json",
        "provenance.json",
        "gate_audit.json",
        "SHA256SUMS",
    ]
    for name in required:
        if not (OUT / name).exists():
            raise RuntimeError(f"missing snapshot artifact: {name}")

    sums = {}
    for line in (OUT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    for name in required[:-1]:
        observed = sha(OUT / name)
        if sums.get(name) != observed:
            raise RuntimeError(f"snapshot hash mismatch: {name}")

    provenance = json.loads((OUT / "provenance.json").read_text(encoding="utf-8"))
    if provenance.get("contract") != "FIRST_POST_ACTIVATION_LIVE_SNAPSHOT_V1":
        raise RuntimeError("unexpected snapshot provenance contract")
    if provenance.get("activation_at") != ACTIVATION:
        raise RuntimeError("activation boundary drift")
    if provenance.get("real_shadow_run_created") is not False:
        raise RuntimeError("45C must not create a shadow run")
    captured_at = pd.Timestamp(provenance["captured_at"])
    if captured_at <= pd.Timestamp(ACTIVATION):
        raise RuntimeError("snapshot was not captured post activation")

    universe = pd.read_csv(OUT / "universe.csv", dtype=str)
    if len(universe) != 100 or universe["ticker"].nunique() != 100:
        raise RuntimeError("universe snapshot is not exactly 100 unique names")

    gate = json.loads((OUT / "gate_audit.json").read_text(encoding="utf-8"))
    if gate.get("contract") != "FIRST_POST_ACTIVATION_LIVE_SNAPSHOT_GATE_AUDIT_V1":
        raise RuntimeError("unexpected gate audit contract")
    if gate.get("shadow_execution_ready") is not False:
        raise RuntimeError("45C snapshot must remain shadow-execution blocked")
    if gate.get("real_shadow_run_created") is not False:
        raise RuntimeError("45C gate audit must not create a shadow run")

    market = pd.read_csv(OUT / "market.csv.gz")
    if market["ticker"].duplicated().any():
        raise RuntimeError("market snapshot has duplicate ticker")
    if not market["ticker"].isin(universe["ticker"]).all():
        raise RuntimeError("market snapshot contains ticker outside universe")
    if provenance["market"]["captured_rows"] != len(market):
        raise RuntimeError("market row count mismatch")
    if provenance["market"]["rejection_count"] + len(market) != 100:
        raise RuntimeError("market capture + rejection count must equal 100")

    print(json.dumps({
        "contract":"FIRST_POST_ACTIVATION_LIVE_SNAPSHOT_VERIFY_V1",
        "captured_at":provenance["captured_at"],
        "universe_members":len(universe),
        "market_rows":len(market),
        "market_rejections":provenance["market"]["rejection_count"],
        "status":"PASS"
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
