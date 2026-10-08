#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
import urllib.request
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from zincir_kiran.corporate_action_bootstrap import classify_share_count_subject
from zincir_kiran.live_high52_reconciliation import (
    High52ReconciliationEvidence,
    evaluate_high52_reconciliation,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPO = "zxc28tarik/TOTAL-RASYO-HESAPLAYICI"
SOURCE_COMMIT = "d0c5ce25832dc94c138fc6141bba8fa8392cd00b"
W6_AUDIT_COMMIT = "0c70e1607832624b1b90a9bf150271ab705a6036"
SOURCE_DIR = "data/backtest_sources/kap_monthly_ca_inventory_v1"
MANIFEST_PATH = f"{SOURCE_DIR}/capture_manifest.json"
MANIFEST_SHA256 = (
    "1935232295360b1026a036e725809e0e73a62253ce07145bbc1f13fd6abd1345"
)
RAW_BASE = (
    f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/"
)
HISTORICAL_END = date(2026, 7, 31)

PRICE_PATH = ROOT / "data/live_shadow/high52_input_ca_risk_v1/price_history.csv.gz"
RECENT_GATE_PATH = ROOT / "data/live_shadow/high52_input_ca_risk_v1/ticker_gate.csv"
OUT = ROOT / "data/live_shadow/high52_historical_ca_reconciliation_v1"


def lf_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest()


def raw_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_bytes(path: str) -> bytes:
    url = RAW_BASE + path
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "zincir-kiran-historical-ca-reconcile/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def write_gzip(path: Path, payload: bytes) -> str:
    zipped = gzip.compress(payload, compresslevel=9, mtime=0)
    path.write_bytes(zipped)
    return raw_sha256(zipped)


def parse_kap_date(value: object) -> date | None:
    try:
        return datetime.strptime(
            str(value),
            "%d.%m.%Y %H:%M:%S",
        ).date()
    except (TypeError, ValueError):
        return None


def split_codes(value: object) -> set[str]:
    if value is None:
        return set()
    text = str(value).strip().upper().replace(";", ",")
    if not text or text in {"NAN", "NONE"}:
        return set()
    return {
        token.strip()
        for token in text.split(",")
        if token.strip()
    }


def build_lookbacks() -> pd.DataFrame:
    prices = pd.read_csv(PRICE_PATH)
    prices["trade_date"] = pd.to_datetime(
        prices["trade_date"], errors="raise"
    ).dt.normalize()
    prices["adj_close"] = pd.to_numeric(prices["adj_close"], errors="coerce")

    rows: list[dict[str, object]] = []
    for ticker, group in prices.groupby("ticker", sort=True):
        usable = group.loc[
            group["adj_close"].notna()
            & np.isfinite(group["adj_close"].astype(float))
            & (group["adj_close"].astype(float) > 0)
        ].sort_values("trade_date")
        total = int(len(usable))
        if total < 252:
            rows.append(
                {
                    "ticker": ticker,
                    "finite_positive_adj_close_observations": total,
                    "lookback_start": None,
                    "lookback_end": None,
                    "historical_start": None,
                    "historical_end": None,
                    "price_history_sufficient": False,
                }
            )
            continue

        latest = usable.tail(252)
        lookback_start = pd.Timestamp(latest.iloc[0]["trade_date"]).date()
        lookback_end = pd.Timestamp(latest.iloc[-1]["trade_date"]).date()
        historical_end = min(lookback_end, HISTORICAL_END)
        historical_start = (
            lookback_start if lookback_start <= historical_end else None
        )
        rows.append(
            {
                "ticker": ticker,
                "finite_positive_adj_close_observations": total,
                "lookback_start": lookback_start,
                "lookback_end": lookback_end,
                "historical_start": historical_start,
                "historical_end": (
                    historical_end if historical_start is not None else None
                ),
                "price_history_sufficient": True,
            }
        )

    out = pd.DataFrame(rows).sort_values("ticker").reset_index(drop=True)
    if len(out) != 100 or out["ticker"].nunique() != 100:
        raise RuntimeError("45E expected exact 100-name 45D price universe")
    return out


def load_recent_risk_ids() -> dict[str, tuple[str, ...]]:
    frame = pd.read_csv(RECENT_GATE_PATH, dtype=str, keep_default_na=False)
    out: dict[str, tuple[str, ...]] = {}
    for row in frame.itertuples(index=False):
        value = str(row.recent_ca_risk_event_ids or "")
        ids = tuple(sorted(x for x in value.split("|") if x))
        out[str(row.ticker)] = ids
    return out


def load_source_manifest() -> tuple[dict, bytes]:
    payload = fetch_bytes(MANIFEST_PATH)
    observed = lf_sha256(payload)
    if observed != MANIFEST_SHA256:
        raise RuntimeError(
            f"W6 manifest SHA mismatch expected={MANIFEST_SHA256} "
            f"observed={observed}"
        )
    manifest = json.loads(payload)
    coverage = manifest.get("coverage", {})
    if coverage.get("complete") is not True:
        raise RuntimeError("W6 manifest does not claim complete coverage")
    if int(coverage.get("windows_failed", -1)) != 0:
        raise RuntimeError("W6 manifest has failed windows")
    if int(coverage.get("windows_at_cap_unsplittable", -1)) != 0:
        raise RuntimeError("W6 manifest has unsplittable cap windows")
    if int(coverage.get("windows_ok", -1)) != 595:
        raise RuntimeError("W6 manifest windows_ok drift")
    return manifest, payload


def selected_windows(
    manifest: dict,
    lookbacks: pd.DataFrame,
) -> list[tuple[str, dict]]:
    starts = [
        value
        for value in lookbacks["historical_start"].dropna().tolist()
    ]
    ends = [
        value
        for value in lookbacks["historical_end"].dropna().tolist()
    ]
    if not starts or not ends:
        raise RuntimeError("no historical 252-day intervals to reconcile")
    global_start = min(starts)
    global_end = max(ends)

    selected: list[tuple[str, dict]] = []
    for key, row in manifest["windows"].items():
        if row.get("status") != "OK":
            continue
        start = date.fromisoformat(row["start"])
        end = date.fromisoformat(row["end"])
        if start <= global_end and end >= global_start:
            selected.append((key, row))

    selected.sort(key=lambda item: item[1]["start"])
    if not selected:
        raise RuntimeError("no W6 windows overlap current 252-day lookbacks")
    return selected


def window_fully_covered(
    start: date,
    end: date,
    covered: list[tuple[date, date]],
) -> bool:
    if start > end:
        return True
    cursor = start
    for left, right in covered:
        if right < cursor:
            continue
        if left > cursor:
            return False
        cursor = max(cursor, right) + pd.Timedelta(days=1).to_pytimedelta()
        if cursor > end:
            return True
    return cursor > end


def fetch_selected_sources(
    selected: list[tuple[str, dict]],
) -> tuple[list[dict], list[dict], list[tuple[date, date]]]:
    source_dir = OUT / "w6"
    source_dir.mkdir(parents=True, exist_ok=True)

    source_rows: list[dict] = []
    all_disclosures: list[dict] = []
    covered: list[tuple[date, date]] = []

    for key, meta in selected:
        path = f"{SOURCE_DIR}/{key}.response.json"
        raw = fetch_bytes(path)
        observed = raw_sha256(raw)
        expected = str(meta["response_sha256"])
        if observed != expected:
            raise RuntimeError(
                f"W6 response SHA mismatch {key}: "
                f"expected={expected} observed={observed}"
            )
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise RuntimeError(f"W6 response shape invalid: {key}")

        frozen_path = source_dir / f"{key}.response.json.gz"
        gzip_sha = write_gzip(frozen_path, raw)
        start = date.fromisoformat(meta["start"])
        end = date.fromisoformat(meta["end"])
        covered.append((start, end))
        all_disclosures.extend(rows)
        source_rows.append(
            {
                "window_key": key,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "row_count": int(meta["row_count"]),
                "ca_row_count": int(meta["ca_row_count"]),
                "request_sha256": meta["request_sha256"],
                "source_response_sha256": expected,
                "frozen_response_gzip_sha256": gzip_sha,
            }
        )

    return source_rows, all_disclosures, covered


def classify_historical_risks(
    disclosures: list[dict],
    lookbacks: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, tuple[str, ...]]]:
    windows = {
        str(row.ticker): (
            row.historical_start,
            row.historical_end,
        )
        for row in lookbacks.itertuples(index=False)
        if row.historical_start is not None
    }
    universe = set(lookbacks["ticker"].astype(str))
    risk_rows: list[dict] = []
    risk_ids: dict[str, set[str]] = {ticker: set() for ticker in universe}

    for item in disclosures:
        classified = classify_share_count_subject(
            str(item.get("subject") or ""),
            str(item.get("summary") or ""),
        )
        if classified is None:
            continue

        event_date = parse_kap_date(item.get("publishDate"))
        if event_date is None:
            continue
        codes = split_codes(item.get("stockCodes"))
        codes |= split_codes(item.get("relatedStocks"))
        affected = sorted(codes & universe)
        if not affected:
            continue

        event_id = str(item.get("disclosureIndex") or "").strip()
        if not event_id:
            raise RuntimeError("classified historical KAP row lacks disclosureIndex")

        for ticker in affected:
            bounds = windows.get(ticker)
            if bounds is None:
                continue
            start, end = bounds
            if not (start <= event_date <= end):
                continue
            risk_ids[ticker].add(event_id)
            risk_rows.append(
                {
                    "ticker": ticker,
                    "event_id": event_id,
                    "publish_date": event_date.isoformat(),
                    "event_type": classified.value,
                    "subject": item.get("subject"),
                    "summary": item.get("summary"),
                    "stock_codes": item.get("stockCodes"),
                    "related_stocks": item.get("relatedStocks"),
                    "resolved_economic_adjustment": False,
                }
            )

    frame = pd.DataFrame(risk_rows)
    if frame.empty:
        frame = pd.DataFrame(
            columns=[
                "ticker",
                "event_id",
                "publish_date",
                "event_type",
                "subject",
                "summary",
                "stock_codes",
                "related_stocks",
                "resolved_economic_adjustment",
            ]
        )
    else:
        frame = (
            frame.sort_values(["ticker", "publish_date", "event_id"])
            .drop_duplicates(["ticker", "event_id"])
            .reset_index(drop=True)
        )

    frozen = {
        ticker: tuple(sorted(ids))
        for ticker, ids in risk_ids.items()
    }
    return frame, frozen


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    lookbacks = build_lookbacks()
    recent_ids = load_recent_risk_ids()
    manifest, manifest_bytes = load_source_manifest()
    selected = selected_windows(manifest, lookbacks)
    source_rows, disclosures, covered = fetch_selected_sources(selected)

    historical_risks, historical_ids = classify_historical_risks(
        disclosures, lookbacks
    )

    gate_rows: list[dict[str, object]] = []
    for row in lookbacks.itertuples(index=False):
        ticker = str(row.ticker)
        sufficient = bool(row.price_history_sufficient)
        if sufficient and row.historical_start is not None:
            coverage_complete = window_fully_covered(
                row.historical_start,
                row.historical_end,
                covered,
            )
        elif sufficient:
            coverage_complete = True
        else:
            coverage_complete = False

        evidence = High52ReconciliationEvidence(
            ticker=ticker,
            finite_positive_adj_close_observations=int(
                row.finite_positive_adj_close_observations
            ),
            historical_ca_coverage_complete=coverage_complete,
            unresolved_historical_ca_event_ids=historical_ids.get(ticker, ()),
            unresolved_recent_ca_event_ids=recent_ids.get(ticker, ()),
        )
        result = evaluate_high52_reconciliation(evidence)
        gate_rows.append(
            {
                "ticker": ticker,
                "finite_positive_adj_close_observations": (
                    evidence.finite_positive_adj_close_observations
                ),
                "lookback_start": row.lookback_start,
                "lookback_end": row.lookback_end,
                "historical_start": row.historical_start,
                "historical_end": row.historical_end,
                "historical_ca_coverage_complete": coverage_complete,
                "historical_ca_risk_event_count": len(
                    evidence.unresolved_historical_ca_event_ids
                ),
                "historical_ca_risk_event_ids": "|".join(
                    evidence.unresolved_historical_ca_event_ids
                ),
                "recent_ca_risk_event_count": len(
                    evidence.unresolved_recent_ca_event_ids
                ),
                "recent_ca_risk_event_ids": "|".join(
                    evidence.unresolved_recent_ca_event_ids
                ),
                "status": result.status.value,
                "factor_input_ready": result.factor_input_ready,
                "score_computation_allowed": result.score_computation_allowed,
                "shadow_signal_allowed": result.shadow_signal_allowed,
                "reason_codes": "|".join(result.reason_codes),
            }
        )

    gate = pd.DataFrame(gate_rows).sort_values("ticker").reset_index(drop=True)
    if len(gate) != 100 or gate["ticker"].nunique() != 100:
        raise RuntimeError("45E combined gate must contain exactly 100 tickers")
    if gate["shadow_signal_allowed"].any():
        raise RuntimeError("45E cannot authorize a real shadow signal")

    lookback_path = OUT / "lookback_windows.csv"
    lookbacks.to_csv(
        lookback_path,
        index=False,
        lineterminator="\n",
        date_format="%Y-%m-%d",
    )

    risks_path = OUT / "historical_ca_risks.csv"
    historical_risks.to_csv(risks_path, index=False, lineterminator="\n")

    gate_path = OUT / "combined_gate.csv"
    gate.to_csv(
        gate_path,
        index=False,
        lineterminator="\n",
        date_format="%Y-%m-%d",
    )

    source_manifest = {
        "contract": "HISTORICAL_HIGH52_W6_SOURCE_SUBSET_V1",
        "source_repository": SOURCE_REPO,
        "source_data_commit": SOURCE_COMMIT,
        "w6_audit_commit": W6_AUDIT_COMMIT,
        "source_manifest_path": MANIFEST_PATH,
        "source_manifest_lf_canonical_sha256": MANIFEST_SHA256,
        "source_manifest_observed_lf_canonical_sha256": lf_sha256(
            manifest_bytes
        ),
        "selected_window_count": len(source_rows),
        "selected_windows": source_rows,
    }
    source_manifest_path = OUT / "w6_source_subset_manifest.json"
    source_manifest_path.write_text(
        json.dumps(source_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    status_counts = {
        str(key): int(value)
        for key, value in gate["status"].value_counts().sort_index().items()
    }
    provenance = {
        "contract": "HISTORICAL_HIGH52_CA_RECONCILIATION_V1",
        "production_ready": False,
        "real_shadow_run_created": False,
        "score_values_computed": False,
        "input_price_package": (
            "data/live_shadow/high52_input_ca_risk_v1/price_history.csv.gz"
        ),
        "source": {
            "repository": SOURCE_REPO,
            "source_data_commit": SOURCE_COMMIT,
            "w6_audit_commit": W6_AUDIT_COMMIT,
            "manifest_sha256": MANIFEST_SHA256,
            "selected_window_count": len(source_rows),
        },
        "lookbacks": {
            "tickers": int(len(lookbacks)),
            "price_sufficient_tickers": int(
                lookbacks["price_history_sufficient"].sum()
            ),
            "historical_interval_min_start": (
                min(
                    lookbacks["historical_start"].dropna()
                ).isoformat()
            ),
            "historical_interval_max_end": (
                max(
                    lookbacks["historical_end"].dropna()
                ).isoformat()
            ),
        },
        "historical_risk": {
            "risk_rows": int(len(historical_risks)),
            "risk_tickers": int(historical_risks["ticker"].nunique()),
        },
        "combined_gate": {
            "status_counts": status_counts,
            "factor_input_ready": int(gate["factor_input_ready"].sum()),
            "score_computation_allowed": int(
                gate["score_computation_allowed"].sum()
            ),
            "shadow_signal_allowed": int(gate["shadow_signal_allowed"].sum()),
        },
        "limitations": [
            "Historical positive disclosures are conservative unresolved risk evidence, not proof of completed economic adjustment.",
            "No ex-date, ratio, cash amount or payment date is invented.",
            "Factor-input-ready means data/reconciliation inputs are sufficient for later score computation; 45E itself computes no score and emits no shadow signal."
        ],
    }
    provenance_path = OUT / "provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    files = [
        lookback_path,
        risks_path,
        gate_path,
        source_manifest_path,
        provenance_path,
    ]
    files.extend(path for path in (OUT / "w6").glob("*") if path.is_file())
    sums = [
        f"{raw_sha256(path.read_bytes())}  {path.relative_to(OUT)}"
        for path in sorted(files, key=lambda item: str(item.relative_to(OUT)))
    ]
    (OUT / "SHA256SUMS").write_text(
        "\n".join(sums) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(provenance, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
