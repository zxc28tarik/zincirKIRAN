#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/live_shadow/corporate_action_economic_resolution_v1"
DETAIL_DIR = PACKAGE / "kap_detail"
QUEUE_PATH = PACKAGE / "event_queue.csv"
OUT_ROWS = PACKAGE / "official_table_cells.csv.gz"
OUT_SUMMARY = PACKAGE / "official_table_cell_summary.json"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def parse_event(event_id: str, raw: bytes) -> list[dict]:
    soup = BeautifulSoup(raw, "html.parser")
    container = (
        soup.select_one(f".notification-body-scale-{event_id}")
        or soup.select_one("#expanded-container")
        or soup
    )
    records: list[dict] = []
    for table_index, table in enumerate(container.find_all("table")):
        classes = " ".join(table.get("class") or [])
        for row_index, tr in enumerate(table.find_all("tr")):
            direct_cells = tr.find_all(["td", "th"], recursive=False)
            if not direct_cells:
                continue
            for cell_index, cell in enumerate(direct_cells):
                text = " ".join(cell.stripped_strings).strip()
                if not text:
                    continue
                field_name = None
                field_node = cell.select_one(".taxonomy-field-name")
                if field_node is not None:
                    field_name = field_node.get_text(" ", strip=True)
                records.append(
                    {
                        "event_id": event_id,
                        "table_index": table_index,
                        "table_classes": classes,
                        "row_index": row_index,
                        "cell_index": cell_index,
                        "cell_text": text,
                        "taxonomy_field_name": field_name,
                    }
                )
    return records


def main() -> int:
    queue = pd.read_csv(QUEUE_PATH, dtype=str, keep_default_na=False)
    event_type = dict(
        zip(
            queue["event_id"].astype(str),
            queue["event_type"].astype(str),
            strict=True,
        )
    )

    all_rows: list[dict] = []
    captured = 0
    for event_id in queue["event_id"].astype(str):
        path = DETAIL_DIR / f"{event_id}.html.gz"
        if not path.exists():
            continue
        captured += 1
        raw = gzip.decompress(path.read_bytes())
        rows = parse_event(event_id, raw)
        for row in rows:
            row["event_type"] = event_type[event_id]
            all_rows.append(row)

    frame = pd.DataFrame(all_rows)
    if frame.empty:
        frame = pd.DataFrame(
            columns=[
                "event_id",
                "event_type",
                "table_index",
                "table_classes",
                "row_index",
                "cell_index",
                "cell_text",
                "taxonomy_field_name",
            ]
        )
    else:
        frame = frame[
            [
                "event_id",
                "event_type",
                "table_index",
                "table_classes",
                "row_index",
                "cell_index",
                "cell_text",
                "taxonomy_field_name",
            ]
        ].sort_values(
            ["event_id", "table_index", "row_index", "cell_index"]
        )

    frame.to_csv(
        OUT_ROWS,
        index=False,
        lineterminator="\n",
        compression={
            "method": "gzip",
            "compresslevel": 9,
            "mtime": 0,
        },
    )

    if frame.empty:
        per_type = {}
    else:
        grouped = frame.groupby("event_type")
        per_type = {
            str(name): {
                "events_with_table_cells": int(group["event_id"].nunique()),
                "cell_records": int(len(group)),
                "events_with_taxonomy_field_name": int(
                    group.loc[
                        group["taxonomy_field_name"].fillna("").astype(str).ne("")
                    ]["event_id"].nunique()
                ),
            }
            for name, group in grouped
        }

    summary = {
        "contract": "KAP_OFFICIAL_TABLE_CELL_DISCOVERY_V1",
        "risk_released": 0,
        "shadow_signal_allowed": False,
        "queue_events": int(len(queue)),
        "official_html_present": int(captured),
        "table_cell_records": int(len(frame)),
        "events_with_table_cells": int(frame["event_id"].nunique()) if not frame.empty else 0,
        "per_event_type": per_type,
        "output_sha256": sha256_bytes(OUT_ROWS.read_bytes()),
    }
    OUT_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
