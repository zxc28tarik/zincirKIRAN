#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/live_shadow/high52_historical_ca_reconciliation_v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    required = [
        "lookback_windows.csv",
        "historical_ca_risks.csv",
        "combined_gate.csv",
        "w6_source_subset_manifest.json",
        "provenance.json",
        "SHA256SUMS",
    ]
    for name in required:
        if not (OUT / name).exists():
            raise RuntimeError(f"missing 45E artifact: {name}")

    sums = {}
    for line in (OUT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest

    for path in OUT.rglob("*"):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        rel = str(path.relative_to(OUT))
        if sums.get(rel) != sha(path):
            raise RuntimeError(f"45E hash mismatch: {rel}")

    source = json.loads(
        (OUT / "w6_source_subset_manifest.json").read_text(encoding="utf-8")
    )
    if source.get("source_manifest_lf_canonical_sha256") != (
        "1935232295360b1026a036e725809e0e73a62253ce07145bbc1f13fd6abd1345"
    ):
        raise RuntimeError("45E W6 source manifest identity drift")

    gate = pd.read_csv(OUT / "combined_gate.csv")
    if len(gate) != 100 or gate["ticker"].nunique() != 100:
        raise RuntimeError("45E combined gate must cover 100 unique tickers")
    if gate["shadow_signal_allowed"].astype(bool).any():
        raise RuntimeError("45E cannot allow a shadow signal")

    lookbacks = pd.read_csv(OUT / "lookback_windows.csv")
    if int(lookbacks["price_history_sufficient"].astype(bool).sum()) != 99:
        raise RuntimeError("45E must preserve 45D's 99/100 price sufficiency")

    provenance = json.loads(
        (OUT / "provenance.json").read_text(encoding="utf-8")
    )
    if provenance.get("real_shadow_run_created") is not False:
        raise RuntimeError("45E cannot create a shadow run")
    if provenance.get("score_values_computed") is not False:
        raise RuntimeError("45E cannot compute factor score values")

    print(
        json.dumps(
            {
                "contract": "HISTORICAL_HIGH52_CA_RECONCILIATION_VERIFY_V1",
                "factor_input_ready": int(
                    gate["factor_input_ready"].astype(bool).sum()
                ),
                "historical_risk_tickers": int(
                    (gate["historical_ca_risk_event_count"] > 0).sum()
                ),
                "recent_risk_tickers": int(
                    (gate["recent_ca_risk_event_count"] > 0).sum()
                ),
                "shadow_signal_allowed": 0,
                "status": "PASS",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
