import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/source_catalogs/current_bist100_q4_2026_v1.json"


def test_q4_catalog_rounds_to_exactly_100_unique_members():
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    anchor = payload["anchor"]
    event = payload["q4_event"]

    members = set(anchor["members"])
    adds = set(event["adds"])
    removes = set(event["removes"])

    assert len(anchor["members"]) == 100
    assert len(members) == 100
    assert len(event["adds"]) == 27
    assert len(adds) == 27
    assert len(event["removes"]) == 27
    assert len(removes) == 27
    assert removes <= members
    assert not (adds & members)

    members -= removes
    members |= adds
    assert len(members) == 100


def test_q4_catalog_source_identity_is_frozen():
    payload = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert payload["anchor"]["source_commit"] == (
        "883e680a2564e38f4c08a21bc88aa62efb95a26a1"
    )
    assert payload["anchor"]["source_sha256"] == (
        "a3b14014aa4d3ff16a082bc0dac64346b906f4b7720aeae5a8c449a2add314f2"
    )
    assert payload["q4_event"]["source_url"].endswith(
        "/15598/bist-pay-endeksleri-donemsel-degisiklikleri"
    )
    assert payload["q4_event"]["effective_date"] == "2026-10-01"
