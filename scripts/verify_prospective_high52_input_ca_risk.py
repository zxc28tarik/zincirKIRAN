#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/live_shadow/high52_input_ca_risk_v1"
ACTIVATION = pd.Timestamp("2026-10-07T22:10:15+00:00")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    required = [
        "price_history.csv.gz",
        "recent_ca_risks.csv",
        "ticker_gate.csv",
        "price_rejections.json",
        "kap_capture_manifest.json",
        "provenance.json",
        "SHA256SUMS",
    ]
    for name in required:
        if not (OUT / name).exists():
            raise RuntimeError(f"missing 45D artifact: {name}")

    sums = {}
    for line in (OUT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    for path in OUT.rglob("*"):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        rel = str(path.relative_to(OUT))
        if sums.get(rel) != sha(path):
            raise RuntimeError(f"45D hash mismatch: {rel}")

    provenance = json.loads((OUT / "provenance.json").read_text(encoding="utf-8"))
    captured_at = pd.Timestamp(provenance["captured_at"])
    if captured_at <= ACTIVATION:
        raise RuntimeError("45D package is not post activation")
    if provenance.get("real_shadow_run_created") is not False:
        raise RuntimeError("45D cannot create a shadow run")

    manifest = json.loads(
        (OUT / "kap_capture_manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("complete") is not True:
        raise RuntimeError("KAP recent-gap coverage is not complete")

    gate = pd.read_csv(OUT / "ticker_gate.csv")
    if len(gate) != 100 or gate["ticker"].nunique() != 100:
        raise RuntimeError("45D gate does not cover exact 100-name universe")
    if gate["shadow_signal_allowed"].astype(bool).any():
        raise RuntimeError("45D must not allow any shadow signal")
    if int((gate["finite_positive_adj_close_observations"] >= 252).sum()) != int(
        provenance["price_history"]["tickers_with_252_adj_close"]
    ):
        raise RuntimeError("45D 252-observation coverage mismatch")

    print(
        json.dumps(
            {
                "contract": "PROSPECTIVE_HIGH52_INPUT_CA_RISK_VERIFY_V1",
                "captured_at": provenance["captured_at"],
                "tickers": len(gate),
                "tickers_with_252_adj_close": int(
                    provenance["price_history"]["tickers_with_252_adj_close"]
                ),
                "recent_ca_gap_complete": True,
                "shadow_signal_allowed": 0,
                "status": "PASS",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
