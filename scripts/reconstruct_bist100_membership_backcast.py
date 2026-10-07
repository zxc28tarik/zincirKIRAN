#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "research/source_catalogs/bist100_membership_backcast_2019_2021_v1.json"
OUTPUT_PATH = ROOT / "research/evidence_runs/bist100_membership_backcast_2019_2021_v1.json"

RAW_BASE = "https://raw.githubusercontent.com/{repo}/{commit}/{path}"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_event_hash(event: dict[str, object]) -> str:
    payload = {
        "event_id": event["event_id"],
        "effective_date": event["effective_date"],
        "adds": sorted(event["adds"]),
        "removes": sorted(event["removes"]),
        "source_url": event.get("source_url"),
        "source_urls": event.get("source_urls"),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_bytes(encoded)


def load_anchor(catalog: dict[str, object]) -> tuple[set[str], dict[str, object]]:
    anchor = catalog["anchor"]
    url = RAW_BASE.format(
        repo=anchor["source_repository"],
        commit=anchor["source_commit"],
        path=anchor["path"],
    )
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    observed = sha256_bytes(payload)
    if observed != anchor["sha256"]:
        raise RuntimeError(
            f"anchor sha mismatch expected={anchor['sha256']} observed={observed}"
        )

    text = payload.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    members: list[str] = []
    for row in reader:
        if (
            row.get("signal_date") == anchor["signal_date"]
            and row.get("index_code") == anchor["expected_index_code"]
        ):
            ticker = str(row.get("ticker") or "").strip().upper()
            if ticker:
                members.append(ticker)

    if len(members) != anchor["expected_member_count"]:
        raise RuntimeError(
            f"anchor row count {len(members)} != {anchor['expected_member_count']}"
        )
    if len(set(members)) != len(members):
        raise RuntimeError("anchor contains duplicate tickers")
    return set(members), {
        "url": url,
        "sha256": observed,
        "signal_date": anchor["signal_date"],
        "member_count": len(members),
    }


def all_events(catalog: dict[str, object]) -> list[dict[str, object]]:
    events = list(catalog["periodic_events"]) + list(catalog["intraperiod_events"])
    for event in events:
        adds = [str(x).strip().upper() for x in event["adds"]]
        removes = [str(x).strip().upper() for x in event["removes"]]
        if not adds or not removes or len(adds) != len(removes):
            raise RuntimeError(f"event must have equal nonzero adds/removes: {event['event_id']}")
        if len(set(adds)) != len(adds) or len(set(removes)) != len(removes):
            raise RuntimeError(f"event has duplicate tickers: {event['event_id']}")
        if set(adds) & set(removes):
            raise RuntimeError(f"event add/remove overlap: {event['event_id']}")
        event["adds"] = adds
        event["removes"] = removes
        event["event_record_sha256"] = canonical_event_hash(event)
    return sorted(events, key=lambda item: (item["effective_date"], item["event_id"]))


def reverse_event(state: set[str], event: dict[str, object]) -> set[str]:
    adds = set(event["adds"])
    removes = set(event["removes"])
    missing_adds = sorted(adds - state)
    unexpected_removes = sorted(removes & state)
    if missing_adds or unexpected_removes:
        raise RuntimeError(
            f"reverse precondition failed {event['event_id']}: "
            f"missing_adds={missing_adds} unexpected_removes={unexpected_removes}"
        )
    out = set(state)
    out.difference_update(adds)
    out.update(removes)
    if len(out) != 100:
        raise RuntimeError(
            f"reverse event {event['event_id']} produced {len(out)} members"
        )
    return out


def forward_event(state: set[str], event: dict[str, object]) -> set[str]:
    adds = set(event["adds"])
    removes = set(event["removes"])
    missing_removes = sorted(removes - state)
    unexpected_adds = sorted(adds & state)
    if missing_removes or unexpected_adds:
        raise RuntimeError(
            f"forward precondition failed {event['event_id']}: "
            f"missing_removes={missing_removes} unexpected_adds={unexpected_adds}"
        )
    out = set(state)
    out.difference_update(removes)
    out.update(adds)
    if len(out) != 100:
        raise RuntimeError(
            f"forward event {event['event_id']} produced {len(out)} members"
        )
    return out


def state_hash(state: set[str]) -> str:
    return sha256_bytes(("\n".join(sorted(state)) + "\n").encode("utf-8"))


def main() -> int:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    anchor, anchor_receipt = load_anchor(catalog)
    events = all_events(catalog)

    reverse_records: list[dict[str, object]] = []
    state = set(anchor)
    reverse_records.append(
        {
            "checkpoint": "ANCHOR_2021_08_02",
            "member_count": len(state),
            "member_set_sha256": state_hash(state),
            "members": sorted(state),
        }
    )
    for event in reversed(events):
        state = reverse_event(state, event)
        reverse_records.append(
            {
                "checkpoint": f"BEFORE_{event['effective_date']}_{event['event_id']}",
                "reversed_event": event["event_id"],
                "member_count": len(state),
                "member_set_sha256": state_hash(state),
                "members": sorted(state),
            }
        )

    earliest = set(state)
    forward_records: list[dict[str, object]] = []
    for event in events:
        state = forward_event(state, event)
        forward_records.append(
            {
                "after_event": event["event_id"],
                "effective_date": event["effective_date"],
                "member_count": len(state),
                "member_set_sha256": state_hash(state),
            }
        )

    if state != anchor:
        missing = sorted(anchor - state)
        extra = sorted(state - anchor)
        raise RuntimeError(
            f"forward replay did not reproduce anchor: missing={missing} extra={extra}"
        )

    receipt = {
        "contract": "BIST100_MEMBERSHIP_BACKCAST_2019_2021_V1",
        "authority": "RECONSTRUCTED_FROM_AUDITABLE_INDEX_EVENTS",
        "production_ready": False,
        "factor_results_recomputed": False,
        "anchor": anchor_receipt,
        "catalog_sha256": sha256_bytes(CATALOG_PATH.read_bytes()),
        "event_count": len(events),
        "periodic_event_count": len(catalog["periodic_events"]),
        "intraperiod_event_count": len(catalog["intraperiod_events"]),
        "event_records": [
            {
                "event_id": event["event_id"],
                "effective_date": event["effective_date"],
                "adds": event["adds"],
                "removes": event["removes"],
                "event_record_sha256": event["event_record_sha256"],
                "source_authority": event.get("source_authority"),
                "evidence_quality": event.get("evidence_quality"),
                "source_url": event.get("source_url"),
                "source_urls": event.get("source_urls"),
            }
            for event in events
        ],
        "earliest_reconstructed_state": {
            "before_event": events[0]["event_id"],
            "member_count": len(earliest),
            "member_set_sha256": state_hash(earliest),
            "members": sorted(earliest),
        },
        "reverse_checkpoints": reverse_records,
        "forward_replay": {
            "event_count": len(forward_records),
            "all_states_member_count_100": all(
                item["member_count"] == 100 for item in forward_records
            ),
            "final_member_set_sha256": state_hash(state),
            "anchor_member_set_sha256": state_hash(anchor),
            "exact_anchor_match": state == anchor,
            "records": forward_records,
        },
        "limitations": [
            "Membership is reconstructed from an Aug-2021 anchor plus index change events; it is not a raw full historical constituent snapshot feed.",
            "Periodic events use primary Borsa Istanbul announcement pages.",
            "Three intra-period events are retained with explicit provenance and evidence-quality labels; direct archival KAP notification IDs are not available for every event in this package.",
            "This implementation does not extend daily prices or financial facts and therefore does not by itself increase usable H252 factor folds.",
            "No factor, model, portfolio, or production parameter is changed."
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
