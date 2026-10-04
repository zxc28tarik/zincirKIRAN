#!/usr/bin/env python3
"""Build a deterministic Evidence Phase manifest from downloaded real artifacts.

Input JSON example:
{
  "snapshot_id": "bist-2026-10-04",
  "as_of": "2026-10-04T12:00:00+00:00",
  "created_at": "2026-10-04T12:05:00+00:00",
  "readiness_spec": {
    "specification_id": "real-pit-v1",
    "definition_version": "v1",
    "preregistered_at": "2026-10-04T10:00:00+00:00",
    "minimum_domain_coverage": {"PRICES": 0.95}
  },
  "allowed_source_ids": ["kap", "borsa_istanbul"],
  "artifacts": [{
    "artifact_id": "prices-2026-10-04",
    "source_id": "borsa_istanbul",
    "source_url": "https://...",
    "domain": "PRICES",
    "path": "downloads/prices.csv",
    "logical_key": "bist:prices:2026-10-04",
    "retrieved_at": "2026-10-04T12:04:00+00:00"
  }],
  "coverage": [{
    "domain": "PRICES",
    "observed_securities": 550,
    "required_securities": 560,
    "observed_periods": 1,
    "required_periods": 1
  }]
}
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from zincir_kiran.evidence_phase import (
    DomainCoverage,
    EvidenceDomain,
    SnapshotReadinessSpec,
    SourceArtifact,
    build_pit_snapshot_manifest,
)


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("all manifest timestamps must be timezone-aware")
    return parsed


def load_artifact(row: dict[str, Any]) -> SourceArtifact:
    path = Path(row["path"])
    content = path.read_bytes()
    return SourceArtifact.from_bytes(
        artifact_id=row["artifact_id"],
        source_id=row["source_id"],
        source_url=row["source_url"],
        domain=EvidenceDomain(row["domain"]),
        retrieved_at=parse_time(row["retrieved_at"]),
        content=content,
        logical_key=row["logical_key"],
        source_published_at=(
            parse_time(row["source_published_at"])
            if row.get("source_published_at")
            else None
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    args = parser.parse_args()

    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    readiness = payload["readiness_spec"]
    thresholds = tuple(
        sorted(
            (
                (EvidenceDomain(domain), float(value))
                for domain, value in readiness["minimum_domain_coverage"].items()
            ),
            key=lambda item: item[0].value,
        )
    )
    specification = SnapshotReadinessSpec(
        specification_id=readiness["specification_id"],
        definition_version=readiness["definition_version"],
        preregistered_at=parse_time(readiness["preregistered_at"]),
        minimum_domain_coverage=thresholds,
    )
    artifacts = [load_artifact(row) for row in payload.get("artifacts", [])]
    coverage = [
        DomainCoverage(
            domain=EvidenceDomain(row["domain"]),
            observed_securities=int(row["observed_securities"]),
            required_securities=int(row["required_securities"]),
            observed_periods=int(row["observed_periods"]),
            required_periods=int(row["required_periods"]),
        )
        for row in payload.get("coverage", [])
    ]
    manifest = build_pit_snapshot_manifest(
        snapshot_id=payload["snapshot_id"],
        created_at=parse_time(payload["created_at"]),
        as_of=parse_time(payload["as_of"]),
        artifacts=artifacts,
        domain_coverage=coverage,
        readiness_spec=specification,
        allowed_source_ids=set(payload["allowed_source_ids"]),
    )
    output = {
        "snapshot_id": manifest.snapshot_id,
        "as_of": manifest.as_of.isoformat(),
        "created_at": manifest.created_at.isoformat(),
        "readiness": manifest.readiness.value,
        "gap_reasons": manifest.gap_reasons,
        "manifest_sha256": manifest.manifest_sha256,
        "artifacts": [
            {
                "artifact_id": item.artifact_id,
                "source_id": item.source_id,
                "domain": item.domain.value,
                "logical_key": item.logical_key,
                "content_sha256": item.content_sha256,
                "byte_size": item.byte_size,
                "retrieved_at": item.retrieved_at.isoformat(),
                "source_published_at": (
                    item.source_published_at.isoformat()
                    if item.source_published_at is not None
                    else None
                ),
                "source_url": item.source_url,
            }
            for item in manifest.source_artifacts
        ],
        "coverage": [
            {
                "domain": item.domain.value,
                "observed_securities": item.observed_securities,
                "required_securities": item.required_securities,
                "observed_periods": item.observed_periods,
                "required_periods": item.required_periods,
                "joint_coverage": item.joint_coverage,
            }
            for item in manifest.domain_coverage
        ],
    }
    Path(args.output_json).write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
