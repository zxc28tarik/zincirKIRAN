#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/research_sources/pre2021_price_extension_v1"
EXPECTED_PRICE_SHA256 = "e0894027610988651d9ffec6cb53cad5bcfc41ae7dbd132d5e55af06c7afcf5e"
EXPECTED_MEMBERSHIP_SHA256 = "ce691744788fb74f8c904b2aa8b34528140d0785e6507989096362bb226c93ab"
EXPECTED_COVERAGE_SHA256 = "97fa22b691c6a5c2c8d27b0cf83b9d6b1aaa034c6eb64aa9bc6f5bc72f044c7f"
EXPECTED_PROVENANCE_SHA256 = "93599a3119d749793329787e75f51598dce7e0c8c4ebded407a635bada228caf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    required = {
        "prices_2018-01_2022-08.csv.gz": EXPECTED_PRICE_SHA256,
        "membership_2020-09_2021-07.csv": EXPECTED_MEMBERSHIP_SHA256,
        "coverage_2020-09_2021-07.csv": EXPECTED_COVERAGE_SHA256,
        "provenance.json": EXPECTED_PROVENANCE_SHA256,
    }
    for name, expected in required.items():
        path = PACKAGE / name
        if not path.exists():
            raise RuntimeError(f"missing frozen artifact: {name}")
        observed = sha(path)
        if observed != expected:
            raise RuntimeError(
                f"frozen artifact drift {name}: expected={expected} observed={observed}"
            )

    sums = {}
    for line in (PACKAGE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        sums[name] = digest
    for name, expected in required.items():
        if sums.get(name) != expected:
            raise RuntimeError(f"SHA256SUMS mismatch for {name}")

    provenance = json.loads((PACKAGE / "provenance.json").read_text(encoding="utf-8"))
    if provenance.get("contract") != "PRE2021_PRICE_EXTENSION_FREEZE_V1":
        raise RuntimeError("unexpected provenance contract")
    if provenance.get("prices", {}).get("deterministic_gzip_sha256") != EXPECTED_PRICE_SHA256:
        raise RuntimeError("provenance price hash mismatch")
    if not provenance.get("acceptance", {}).get("all_11_target_months_pass"):
        raise RuntimeError("frozen coverage acceptance is not true")

    membership = pd.read_csv(PACKAGE / "membership_2020-09_2021-07.csv")
    if len(membership) != 1100:
        raise RuntimeError(f"membership rows != 1100: {len(membership)}")
    counts = membership.groupby("signal_date")["ticker"].nunique()
    if len(counts) != 11 or not counts.eq(100).all():
        raise RuntimeError("membership is not exactly 100 names across 11 months")

    coverage = pd.read_csv(PACKAGE / "coverage_2020-09_2021-07.csv")
    tested = coverage.groupby("signal_date")["h252_test_cell_eligible"].sum()
    if len(tested) != 11 or int(tested.min()) < 20:
        raise RuntimeError(
            f"frozen coverage gate failed: months={len(tested)} min={tested.min()}"
        )

    print(json.dumps({
        "contract":"PRE2021_PRICE_EXTENSION_FREEZE_VERIFY_V1",
        "frozen_price_sha256":EXPECTED_PRICE_SHA256,
        "membership_months":int(len(counts)),
        "membership_min_names":int(counts.min()),
        "h252_test_min_cells":int(tested.min()),
        "h252_test_max_cells":int(tested.max()),
        "status":"PASS"
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
