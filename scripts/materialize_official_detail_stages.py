#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from zincir_kiran.corporate_action_detail_stage import (
    OfficialDetailStageEvidence,
    classify_official_detail_stage,
)

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/live_shadow/corporate_action_economic_resolution_v1"
QUEUE = PACKAGE / "event_queue.csv"
PARSED = PACKAGE / "parsed_detail"
OUT = PACKAGE / "detail_stage.csv"
SUMMARY = PACKAGE / "detail_stage_summary.json"


def main() -> int:
    queue = pd.read_csv(QUEUE, dtype=str, keep_default_na=False)
    rows: list[dict[str, object]] = []

    for item in queue.itertuples(index=False):
        event_id = str(item.event_id)
        path = PARSED / f"{event_id}.json"
        if not path.exists():
            rows.append(
                {
                    "event_id": event_id,
                    "event_type": str(item.event_type),
                    "official_detail_present": False,
                    "stage": "DETAIL_MISSING",
                    "reason_code": "OFFICIAL_DETAIL_NOT_CAPTURED",
                    "risk_released": False,
                }
            )
            continue

        payload = json.loads(path.read_text(encoding="utf-8"))
        basic = payload.get("basic") or {}
        result = classify_official_detail_stage(
            OfficialDetailStageEvidence(
                event_id=event_id,
                event_type=str(item.event_type),
                title=str(basic.get("title") or ""),
                summary=(
                    str(basic.get("summary"))
                    if basic.get("summary") is not None
                    else None
                ),
            )
        )
        rows.append(
            {
                "event_id": event_id,
                "event_type": str(item.event_type),
                "official_detail_present": True,
                "stage": result.stage.value,
                "reason_code": result.reason_code,
                "risk_released": result.risk_released,
            }
        )

    frame = pd.DataFrame(rows).sort_values("event_id").reset_index(drop=True)
    if len(frame) != 400 or frame["event_id"].nunique() != 400:
        raise RuntimeError("detail-stage inventory must contain exactly 400 events")
    if frame["risk_released"].astype(bool).any():
        raise RuntimeError("detail-stage triage cannot release event risk")

    frame.to_csv(OUT, index=False, lineterminator="\n")

    summary = {
        "contract": "OFFICIAL_KAP_DETAIL_STAGE_TRIAGE_V1",
        "events": 400,
        "risk_released": 0,
        "status_counts": {
            str(key): int(value)
            for key, value in frame["stage"].value_counts().sort_index().items()
        },
        "per_event_type": {
            str(event_type): {
                str(key): int(value)
                for key, value in group["stage"].value_counts().sort_index().items()
            }
            for event_type, group in frame.groupby("event_type", sort=True)
        },
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
