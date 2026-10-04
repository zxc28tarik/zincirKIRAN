#!/usr/bin/env python3
"""Validate locally staged cross-project artifacts for the experimental Factor Lab."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from zincir_kiran.experimental_dataset import (
    default_experimental_factor_dataset_manifest,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "staging_dir",
        help="Directory containing files named by artifact_id or mapped in mapping JSON.",
    )
    parser.add_argument(
        "--mapping-json",
        help="Optional JSON object mapping artifact_id to relative file path.",
    )
    parser.add_argument("--receipt", default="experimental_dataset_validation.json")
    args = parser.parse_args()

    root = Path(args.staging_dir)
    mapping = {}
    if args.mapping_json:
        mapping = json.loads(Path(args.mapping_json).read_text(encoding="utf-8"))
        if not isinstance(mapping, dict):
            raise ValueError("mapping JSON must be an object")

    manifest = default_experimental_factor_dataset_manifest()
    rows = []
    failures = []
    for artifact in manifest.inputs:
        relative = mapping.get(artifact.artifact_id, artifact.artifact_id)
        path = root / relative
        if not path.is_file():
            failures.append(f"MISSING:{artifact.artifact_id}:{path}")
            rows.append(
                {
                    "artifact_id": artifact.artifact_id,
                    "path": str(path),
                    "status": "MISSING",
                    "expected_sha256": artifact.sha256,
                }
            )
            continue
        observed = sha256(path)
        status = "PASS" if observed == artifact.sha256 else "HASH_MISMATCH"
        if status != "PASS":
            failures.append(
                f"HASH_MISMATCH:{artifact.artifact_id}:{observed}!={artifact.sha256}"
            )
        rows.append(
            {
                "artifact_id": artifact.artifact_id,
                "path": str(path),
                "status": status,
                "expected_sha256": artifact.sha256,
                "observed_sha256": observed,
                "size_bytes": path.stat().st_size,
                "authority": artifact.authority,
            }
        )

    receipt = {
        "dataset_id": manifest.dataset_id,
        "authority": manifest.authority.value,
        "result": "PASS" if not failures else "BLOCKED",
        "failures": failures,
        "artifacts": rows,
    }
    Path(args.receipt).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit("\n".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
