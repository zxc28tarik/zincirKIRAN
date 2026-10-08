#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/live_shadow/corporate_action_economic_resolution_v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    required = [
        "event_queue.csv",
        "detail_capture.csv",
        "taxonomy_fields.csv",
        "excel_capture.csv",
        "excel_cells.csv.gz",
        "yahoo_actions.csv",
        "initial_resolution.csv",
        "provenance.json",
        "SHA256SUMS",
    ]
    for name in required:
        if not (OUT / name).exists():
            raise RuntimeError(f"missing 45F artifact: {name}")

    sums = {}
    for line in (OUT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    for path in OUT.rglob("*"):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        rel = str(path.relative_to(OUT))
        if sums.get(rel) != sha(path):
            raise RuntimeError(f"45F hash mismatch: {rel}")

    queue = pd.read_csv(OUT / "event_queue.csv", dtype=str)
    if len(queue) != 400 or queue["event_id"].nunique() != 400:
        raise RuntimeError("45F event queue must have exactly 400 unique events")

    excel = pd.read_csv(OUT / "excel_capture.csv")
    if len(excel) != 400 or excel["event_id"].nunique() != 400:
        raise RuntimeError(
            "45F Excel capture table must have exactly 400 unique events"
        )

    initial = pd.read_csv(OUT / "initial_resolution.csv")
    if len(initial) != 400 or initial["event_id"].nunique() != 400:
        raise RuntimeError(
            "45F initial resolution must have exactly 400 unique events"
        )
    if initial["risk_released"].astype(bool).any():
        raise RuntimeError("45F field-discovery run cannot release risk")
    if initial["shadow_signal_allowed"].astype(bool).any():
        raise RuntimeError("45F cannot allow shadow signals")

    provenance = json.loads((OUT / "provenance.json").read_text(encoding="utf-8"))
    if provenance.get("risk_released") != 0:
        raise RuntimeError("45F discovery provenance unexpectedly releases risk")
    if provenance.get("real_shadow_run_created") is not False:
        raise RuntimeError("45F cannot create a shadow run")

    print(
        json.dumps(
            {
                "contract": "CORPORATE_ACTION_ECONOMIC_RESOLUTION_FIELD_DISCOVERY_VERIFY_V1",
                "unique_events": 400,
                "official_detail_captured": provenance["official_detail"]["captured"],
                "official_detail_failed": provenance["official_detail"]["failed"],
                "taxonomy_field_records": provenance["official_detail"]["field_records"],
                "official_excel_captured": provenance.get(
                    "official_excel", {}
                ).get("captured", 0),
                "official_excel_failed": provenance.get(
                    "official_excel", {}
                ).get("failed", 400),
                "official_excel_cell_records": provenance.get(
                    "official_excel", {}
                ).get("cell_records", 0),
                "vendor_corroborated_events": provenance["vendor_corroboration"][
                    "events_with_nearby_vendor_action"
                ],
                "risk_released": 0,
                "status": "PASS",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
