"""Validation helpers for source-backed research fixtures."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from zincir_kiran.pit import require_aware_timestamp


def validate_kap_fixture(path: Path) -> int:
    """Validate that every fixture row has an explicit timezone-aware timestamp."""
    count = 0
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = datetime.fromisoformat(row["publication_timestamp"])
            require_aware_timestamp(timestamp)
            if not row["source_url"].startswith("https://kap.org.tr/"):
                raise ValueError("fixture row must preserve official KAP provenance")
            count += 1
    return count
