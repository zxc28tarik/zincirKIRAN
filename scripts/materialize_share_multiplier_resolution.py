#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from zincir_kiran.corporate_action_economic_resolution import (
    EconomicResolutionEvidence,
    resolve_economic_action,
)
from zincir_kiran.share_multiplier_resolution import (
    extract_share_multiplier_contract,
)

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/live_shadow/corporate_action_economic_resolution_v1"
QUEUE = PACKAGE / "event_queue.csv"
CELLS = PACKAGE / "official_table_cells.csv.gz"
DETAIL_STAGE = PACKAGE / "detail_stage.csv"
OUT = PACKAGE / "share_multiplier_resolution.csv"
SUMMARY = PACKAGE / "share_multiplier_resolution_summary.json"

TARGET_EVENT_TYPE = "BONUS_ISSUE_DISCLOSURE"


def main() -> int:
    queue = pd.read_csv(QUEUE, dtype=str, keep_default_na=False)
    cells = pd.read_csv(CELLS, dtype=str, keep_default_na=False)
    detail_stage = pd.read_csv(DETAIL_STAGE, dtype=str, keep_default_na=False)

    bonus = queue.loc[queue["event_type"].eq(TARGET_EVENT_TYPE)].copy()
    if len(bonus) != 33:
        raise RuntimeError(f"expected 33 bonus-issue events, found {len(bonus)}")

    stage_by_id = {
        str(row.event_id): row
        for row in detail_stage.itertuples(index=False)
    }
    cells_by_id = {
        str(event_id): group.to_dict("records")
        for event_id, group in cells.groupby("event_id", sort=False)
    }

    rows: list[dict] = []
    for row in bonus.itertuples(index=False):
        event_id = str(row.event_id)
        tickers = [x for x in str(row.tickers).split("|") if x]
        stage = stage_by_id[event_id]
        official_present = str(stage.official_detail_present).lower() == "true"

        if len(tickers) != 1:
            rows.append(
                {
                    "event_id": event_id,
                    "tickers": str(row.tickers),
                    "official_detail_present": official_present,
                    "matched_target_rows": 0,
                    "effective_date": "",
                    "effective_date_finalized": False,
                    "bonus_rate_percent": "",
                    "contract_complete": False,
                    "resolution_status": "UNRESOLVED_OFFICIAL_DETAIL_INSUFFICIENT",
                    "risk_released": False,
                    "reason_codes": "MULTI_TICKER_EVENT_NOT_SUPPORTED_BY_V1_CONTRACT",
                }
            )
            continue

        if not official_present:
            evidence = EconomicResolutionEvidence(
                event_id=event_id,
                event_type=TARGET_EVENT_TYPE,
                official_detail_captured=False,
                official_detail_sha256=None,
                official_economic_fields_complete=False,
                official_non_price_affecting_explicit=False,
                vendor_corroboration_present=False,
                source_conflict=False,
            )
            resolution = resolve_economic_action(evidence)
            rows.append(
                {
                    "event_id": event_id,
                    "tickers": tickers[0],
                    "official_detail_present": False,
                    "matched_target_rows": 0,
                    "effective_date": "",
                    "effective_date_finalized": False,
                    "bonus_rate_percent": "",
                    "contract_complete": False,
                    "resolution_status": resolution.status.value,
                    "risk_released": resolution.risk_released,
                    "reason_codes": "|".join(resolution.reason_codes),
                }
            )
            continue

        event_cells = cells_by_id.get(event_id, [])
        extraction = extract_share_multiplier_contract(
            event_cells,
            ticker=tickers[0],
        )

        # The table-cell artifact is derived from captured official KAP HTML.
        # 45F does not need to re-use the raw content hash here; the upstream
        # package hashes and SHA256SUMS preserve byte identity.
        evidence = EconomicResolutionEvidence(
            event_id=event_id,
            event_type=TARGET_EVENT_TYPE,
            official_detail_captured=True,
            official_detail_sha256="0" * 64,
            official_economic_fields_complete=extraction.contract.complete,
            official_non_price_affecting_explicit=False,
            vendor_corroboration_present=False,
            source_conflict=False,
        )
        resolution = resolve_economic_action(evidence)
        reasons = sorted(
            set(extraction.extraction_reason_codes)
            | set(extraction.contract.reason_codes)
            | set(resolution.reason_codes)
        )

        rows.append(
            {
                "event_id": event_id,
                "tickers": tickers[0],
                "official_detail_present": True,
                "matched_target_rows": extraction.matched_target_rows,
                "effective_date": extraction.evidence.effective_date or "",
                "effective_date_finalized": extraction.evidence.effective_date_finalized,
                "bonus_rate_percent": (
                    ""
                    if extraction.evidence.bonus_rate_percent is None
                    else extraction.evidence.bonus_rate_percent
                ),
                "contract_complete": extraction.contract.complete,
                "resolution_status": resolution.status.value,
                "risk_released": resolution.risk_released,
                "reason_codes": "|".join(reasons),
            }
        )

    frame = pd.DataFrame(rows).sort_values("event_id").reset_index(drop=True)
    frame.to_csv(OUT, index=False, lineterminator="\n")

    released = frame["risk_released"].astype(bool)
    summary = {
        "contract": "SHARE_MULTIPLIER_V1",
        "event_type": TARGET_EVENT_TYPE,
        "event_count": int(len(frame)),
        "official_detail_present": int(
            frame["official_detail_present"].astype(bool).sum()
        ),
        "contract_complete": int(
            frame["contract_complete"].astype(bool).sum()
        ),
        "risk_released": int(released.sum()),
        "unresolved": int((~released).sum()),
        "shadow_signal_allowed": False,
        "production_ready": False,
        "reason_counts": {
            reason: int(count)
            for reason, count in (
                frame["reason_codes"]
                .fillna("")
                .astype(str)
                .str.split("|")
                .explode()
                .loc[lambda s: s.ne("")]
                .value_counts()
                .sort_index()
                .items()
            )
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
