#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import io
import json
import urllib.request
from collections import Counter
from pathlib import Path

COMMIT = "c8b481e79e270f2c095e8c180671a3f483f0775e"
BASE = (
    "https://raw.githubusercontent.com/"
    "zxc28tarik/TOTAL-RASYO-HESAPLAYICI/"
    f"{COMMIT}/"
)
SOURCES = (
    (
        "semantic-primary",
        "data/backtest_sources/experimental_semantic_facts_v1/semantic_reports.jsonl.gz",
        "07863ddbd78924ad276e7d0aeba7fa6eec9733477b4ca3c02ece285bcf1d9e7a",
    ),
    (
        "semantic-alias",
        "data/backtest_sources/experimental_semantic_facts_v1/semantic_alias_reports.jsonl.gz",
        "adb49330f29b370306d69545db1a48d34a5fda6d763a4d4bdfd2eadc56df06a3",
    ),
    (
        "semantic-entity",
        "data/backtest_sources/experimental_semantic_facts_v1/semantic_entity_reports.jsonl.gz",
        "d70e8a1056fd16b03a9ba44c8d6d3c183cb9e2f3604f45692d90817e5b52d741",
    ),
)


def fetch(path: str, sha256: str) -> bytes:
    with urllib.request.urlopen(BASE + path, timeout=120) as response:
        payload = response.read()
    observed = hashlib.sha256(payload).hexdigest()
    if observed != sha256:
        raise RuntimeError(f"hash mismatch {path}: {observed}")
    return payload


def main() -> int:
    report_keys: Counter[str] = Counter()
    top_keys: Counter[str] = Counter()
    fact_keys: Counter[str] = Counter()
    canonical_fields: Counter[str] = Counter()
    n_reports = 0
    n_facts = 0
    samples: list[dict[str, object]] = []

    for source_id, path, digest in SOURCES:
        payload = fetch(path, digest)
        with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as gz:
            for raw in gz:
                row = json.loads(raw)
                n_reports += 1
                top_keys.update(row.keys())
                report = row.get("report") or {}
                if isinstance(report, dict):
                    report_keys.update(report.keys())
                facts = row.get("facts") or []
                if not isinstance(facts, list):
                    raise RuntimeError("facts must be a list")
                n_facts += len(facts)
                for fact in facts:
                    if not isinstance(fact, dict):
                        raise RuntimeError("fact must be an object")
                    fact_keys.update(fact.keys())
                    field = (
                        fact.get("canonical_field")
                        or fact.get("fact_code")
                        or fact.get("field")
                    )
                    if field:
                        canonical_fields[str(field)] += 1
                if len(samples) < 5:
                    samples.append(
                        {
                            "source_id": source_id,
                            "top": row,
                        }
                    )

    output = {
        "contract": "EXPERIMENTAL_SEMANTIC_SCHEMA_INSPECTION_V1",
        "source_commit": COMMIT,
        "reports": n_reports,
        "facts": n_facts,
        "top_level_keys": sorted(top_keys),
        "report_keys": sorted(report_keys),
        "fact_keys": sorted(fact_keys),
        "canonical_fields": dict(sorted(canonical_fields.items())),
        "samples": samples,
    }
    path = Path("research/evidence_runs/semantic_schema_inspection_v1.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k != "samples"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
