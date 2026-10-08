#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/live_shadow/high52_input_ca_risk_v1"
UNIVERSE_PATH = (
    ROOT
    / "data/live_shadow/first_post_activation_live_snapshot_v1/universe.csv"
)
ACTIVATION = datetime.fromisoformat("2026-10-07T22:10:15+00:00")
KAP_URL = "https://kap.org.tr/tr/api/disclosure/members/byCriteria"
CA_START = date(2026, 8, 1)
PRICE_START = "2025-07-01"
SAFE_MARGIN = 1900
HARD_CAP = 2000

import sys

SCRIPTS = ROOT / "src"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from zincir_kiran.corporate_action_bootstrap import (  # noqa: E402
    classify_share_count_subject,
)
from zincir_kiran.live_high52_gate import (  # noqa: E402
    High52InputEvidence,
    evaluate_high52_input,
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def encode_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def write_gzip(path: Path, payload: bytes) -> str:
    zipped = gzip.compress(payload, compresslevel=9, mtime=0)
    path.write_bytes(zipped)
    return sha256_bytes(zipped)


def kap_payload(start: date, end: date) -> dict:
    return {
        "fromDate": start.isoformat(),
        "toDate": end.isoformat(),
        "memberType": "",
        "mkkMemberOidList": [],
        "inactiveMkkMemberOidList": [],
        "disclosureClass": "",
        "subjectList": [],
        "isLate": "",
        "mainSector": "",
        "sector": "",
        "subSector": "",
        "marketOid": "",
        "index": "",
        "bdkReview": "",
        "bdkMemberOidList": [],
        "year": "",
        "term": "",
        "ruleType": "",
        "period": "",
        "fromSrc": False,
        "srcCategory": "",
        "disclosureIndexList": [],
    }


def fetch_kap_window(
    start: date,
    end: date,
    *,
    max_attempts: int = 4,
) -> dict:
    request_bytes = encode_json(kap_payload(start, end))
    last_error: str | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                KAP_URL,
                data=request_bytes,
                headers={
                    "Content-Type": "application/json",
                    "Accept-Language": "tr",
                    "User-Agent": "zincir-kiran-shadow-ca-gap/1.0",
                },
                timeout=60,
            )
            if response.status_code == 200:
                raw = response.content
                rows = json.loads(raw)
                if not isinstance(rows, list):
                    raise ValueError(
                        f"UNEXPECTED_RESPONSE_SHAPE:{type(rows).__name__}"
                    )
                return {
                    "status": "OK",
                    "rows": rows,
                    "raw": raw,
                    "request_bytes": request_bytes,
                    "response_http_date": response.headers.get("Date"),
                    "attempt": attempt,
                }
            last_error = f"HTTP_{response.status_code}"
        except Exception as exc:  # noqa: BLE001 - recorded in receipt
            last_error = f"{type(exc).__name__}:{exc}"
        time.sleep(min(2**attempt, 15))
    return {
        "status": "FAILED",
        "error": last_error,
        "request_bytes": request_bytes,
    }


def capture_kap_range(
    start: date,
    end: date,
    *,
    records: list[dict],
    depth: int = 0,
) -> None:
    result = fetch_kap_window(start, end)
    if result["status"] != "OK":
        raise RuntimeError(
            f"KAP window failed {start}..{end}: {result.get('error')}"
        )

    rows = result["rows"]
    if len(rows) >= SAFE_MARGIN and start != end:
        mid = start + (end - start) // 2
        capture_kap_range(start, mid, records=records, depth=depth + 1)
        capture_kap_range(
            mid + timedelta(days=1),
            end,
            records=records,
            depth=depth + 1,
        )
        return

    if len(rows) >= HARD_CAP:
        raise RuntimeError(
            f"KAP single-day/window cap prevents completeness {start}..{end}"
        )

    records.append(
        {
            "start": start,
            "end": end,
            "rows": rows,
            "raw": result["raw"],
            "request_bytes": result["request_bytes"],
            "response_http_date": result.get("response_http_date"),
            "attempt": result["attempt"],
        }
    )


def capture_kap_gap(end: date) -> tuple[list[dict], list[dict]]:
    records: list[dict] = []
    cursor = CA_START
    while cursor <= end:
        window_end = min(cursor + timedelta(days=6), end)
        capture_kap_range(cursor, window_end, records=records)
        cursor = window_end + timedelta(days=1)

    records.sort(key=lambda row: (row["start"], row["end"]))
    expected = CA_START
    for row in records:
        if row["start"] != expected:
            raise RuntimeError(
                f"KAP coverage gap expected={expected} got={row['start']}"
            )
        expected = row["end"] + timedelta(days=1)
    if expected != end + timedelta(days=1):
        raise RuntimeError("KAP coverage does not reach requested end date")

    all_rows: list[dict] = []
    for row in records:
        all_rows.extend(row["rows"])
    return records, all_rows


def _normalize_download(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    symbol = f"{ticker}.IS"
    if (
        frame.empty
        or not isinstance(frame.columns, pd.MultiIndex)
        or symbol not in frame.columns.get_level_values(0)
    ):
        return pd.DataFrame()

    rows = frame[symbol].copy().reset_index()
    date_col = "Date" if "Date" in rows.columns else rows.columns[0]
    dates = pd.to_datetime(rows[date_col], errors="coerce")
    try:
        dates = dates.dt.tz_localize(None)
    except TypeError:
        dates = dates.dt.tz_convert(None)
    rows["trade_date"] = dates.dt.normalize()

    for source, target in (
        ("Close", "raw_close"),
        ("Adj Close", "adj_close"),
        ("Volume", "volume"),
    ):
        rows[target] = pd.to_numeric(rows.get(source), errors="coerce")

    rows["ticker"] = ticker
    rows["source_symbol"] = symbol
    rows["auto_adjust"] = False
    return (
        rows[
            [
                "ticker",
                "source_symbol",
                "trade_date",
                "raw_close",
                "adj_close",
                "volume",
                "auto_adjust",
            ]
        ]
        .dropna(subset=["trade_date"])
        .sort_values("trade_date")
        .drop_duplicates(["ticker", "trade_date"], keep="last")
        .reset_index(drop=True)
    )


def capture_price_history(
    tickers: list[str],
    *,
    end_exclusive: date,
) -> tuple[pd.DataFrame, list[dict]]:
    frames: list[pd.DataFrame] = []
    failures: list[dict] = []

    chunk_size = 40
    for offset in range(0, len(tickers), chunk_size):
        batch = tickers[offset : offset + chunk_size]
        symbols = [f"{ticker}.IS" for ticker in batch]
        try:
            downloaded = yf.download(
                symbols,
                start=PRICE_START,
                end=end_exclusive.isoformat(),
                auto_adjust=False,
                actions=True,
                repair=False,
                progress=False,
                threads=True,
                group_by="ticker",
            )
        except Exception as exc:
            failures.extend(
                {
                    "ticker": ticker,
                    "reason": f"DOWNLOAD:{type(exc).__name__}",
                }
                for ticker in batch
            )
            continue

        for ticker in batch:
            rows = _normalize_download(downloaded, ticker)
            if rows.empty:
                failures.append(
                    {"ticker": ticker, "reason": "NO_PRICE_HISTORY"}
                )
            else:
                frames.append(rows)

    if not frames:
        return pd.DataFrame(), sorted(
            failures, key=lambda row: row["ticker"]
        )
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["ticker", "trade_date"]).reset_index(drop=True)
    return out, sorted(failures, key=lambda row: row["ticker"])


def split_codes(value: object) -> set[str]:
    if value is None:
        return set()
    text = str(value).strip().upper()
    if not text or text in {"NAN", "NONE"}:
        return set()
    normalized = text.replace(";", ",")
    return {
        token.strip()
        for token in normalized.split(",")
        if token.strip()
    }


def build_recent_ca_risks(
    rows: list[dict],
    universe: set[str],
) -> tuple[pd.DataFrame, dict[str, tuple[str, ...]]]:
    risk_rows: list[dict] = []
    by_ticker: dict[str, set[str]] = {ticker: set() for ticker in universe}

    for row in rows:
        if row.get("disclosureType") != "CA":
            continue
        codes = split_codes(row.get("stockCodes"))
        codes |= split_codes(row.get("relatedStocks"))
        affected = sorted(codes & universe)
        if not affected:
            continue

        classified = classify_share_count_subject(
            str(row.get("subject") or ""),
            str(row.get("summary") or ""),
        )
        if classified is None:
            continue

        event_id = str(row.get("disclosureIndex") or "").strip()
        if not event_id:
            raise RuntimeError("classified KAP CA row lacks disclosureIndex")

        for ticker in affected:
            by_ticker[ticker].add(event_id)
            risk_rows.append(
                {
                    "ticker": ticker,
                    "event_id": event_id,
                    "publish_date": row.get("publishDate"),
                    "event_type": classified.value,
                    "subject": row.get("subject"),
                    "summary": row.get("summary"),
                    "stock_codes": row.get("stockCodes"),
                    "related_stocks": row.get("relatedStocks"),
                    "resolved_economic_adjustment": False,
                }
            )

    risk_frame = pd.DataFrame(risk_rows)
    if not risk_frame.empty:
        risk_frame = (
            risk_frame.sort_values(["ticker", "event_id"])
            .drop_duplicates(["ticker", "event_id"])
            .reset_index(drop=True)
        )

    frozen = {
        ticker: tuple(sorted(events))
        for ticker, events in by_ticker.items()
    }
    return risk_frame, frozen


def main() -> int:
    captured_at = datetime.now(UTC)
    if captured_at <= ACTIVATION:
        raise RuntimeError("45D capture must be post activation")

    local_date = captured_at.astimezone(ZoneInfo("Europe/Istanbul")).date()
    end_exclusive = local_date + timedelta(days=1)

    universe = pd.read_csv(UNIVERSE_PATH, dtype=str)
    tickers = sorted(
        set(universe["ticker"].astype(str).str.strip().str.upper())
    )
    if len(tickers) != 100:
        raise RuntimeError("45D requires exact 100-name 45C universe")

    OUT.mkdir(parents=True, exist_ok=True)
    kap_dir = OUT / "kap"
    kap_dir.mkdir(parents=True, exist_ok=True)

    price_history, price_failures = capture_price_history(
        tickers,
        end_exclusive=end_exclusive,
    )
    if price_history.empty:
        raise RuntimeError("price history capture returned no rows")

    kap_records, kap_rows = capture_kap_gap(local_date)

    kap_manifest_rows: list[dict] = []
    for row in kap_records:
        label = f"{row['start'].isoformat()}_{row['end'].isoformat()}"
        request_path = kap_dir / f"{label}.request.json"
        response_path = kap_dir / f"{label}.response.json.gz"
        request_path.write_bytes(row["request_bytes"])
        response_gzip_sha = write_gzip(response_path, row["raw"])
        kap_manifest_rows.append(
            {
                "start": row["start"].isoformat(),
                "end": row["end"].isoformat(),
                "row_count": len(row["rows"]),
                "ca_row_count": sum(
                    1
                    for item in row["rows"]
                    if item.get("disclosureType") == "CA"
                ),
                "request_sha256": sha256_bytes(row["request_bytes"]),
                "response_raw_sha256": sha256_bytes(row["raw"]),
                "response_gzip_sha256": response_gzip_sha,
                "response_http_date": row["response_http_date"],
                "attempt": row["attempt"],
            }
        )

    risk_frame, recent_risk_ids = build_recent_ca_risks(
        kap_rows, set(tickers)
    )

    price_counts = {}
    for ticker, group in price_history.groupby("ticker"):
        adj = pd.to_numeric(group["adj_close"], errors="coerce")
        valid = int(((adj.notna()) & (adj > 0)).sum())
        price_counts[ticker] = {
            "observations": int(len(group)),
            "finite_positive_adj_close": valid,
            "latest_trade_date": (
                pd.Timestamp(group["trade_date"].max()).date().isoformat()
            ),
        }

    gate_rows: list[dict] = []
    for ticker in tickers:
        stats = price_counts.get(
            ticker,
            {
                "observations": 0,
                "finite_positive_adj_close": 0,
                "latest_trade_date": None,
            },
        )
        evidence = High52InputEvidence(
            ticker=ticker,
            adj_close_observations=int(stats["observations"]),
            finite_positive_adj_close_observations=int(
                stats["finite_positive_adj_close"]
            ),
            recent_ca_coverage_complete=True,
            unresolved_recent_ca_event_ids=recent_risk_ids.get(ticker, ()),
            # Historical Aug-2025..Jul-2026 reconciliation is deliberately
            # a separate future step. 45D cannot silently assume it.
            historical_ca_lookback_reconciled=False,
        )
        result = evaluate_high52_input(evidence)
        gate_rows.append(
            {
                "ticker": ticker,
                "adj_close_observations": evidence.adj_close_observations,
                "finite_positive_adj_close_observations": (
                    evidence.finite_positive_adj_close_observations
                ),
                "latest_trade_date": stats["latest_trade_date"],
                "recent_ca_risk_event_count": len(
                    evidence.unresolved_recent_ca_event_ids
                ),
                "recent_ca_risk_event_ids": "|".join(
                    evidence.unresolved_recent_ca_event_ids
                ),
                "historical_ca_lookback_reconciled": False,
                "status": result.status.value,
                "score_computation_allowed": result.score_computation_allowed,
                "shadow_signal_allowed": result.shadow_signal_allowed,
                "reason_codes": "|".join(result.reason_codes),
            }
        )

    gate = pd.DataFrame(gate_rows).sort_values("ticker").reset_index(drop=True)
    if gate["shadow_signal_allowed"].any():
        raise RuntimeError("45D is forbidden from emitting shadow signals")

    price_path = OUT / "price_history.csv.gz"
    price_bytes = price_history.to_csv(
        index=False,
        lineterminator="\n",
        date_format="%Y-%m-%d",
    ).encode("utf-8")
    price_sha = write_gzip(price_path, price_bytes)

    risk_path = OUT / "recent_ca_risks.csv"
    if risk_frame.empty:
        risk_path.write_text(
            "ticker,event_id,publish_date,event_type,subject,summary,"
            "stock_codes,related_stocks,resolved_economic_adjustment\n",
            encoding="utf-8",
        )
    else:
        risk_frame.to_csv(risk_path, index=False, lineterminator="\n")

    gate_path = OUT / "ticker_gate.csv"
    gate.to_csv(gate_path, index=False, lineterminator="\n")

    rejection_path = OUT / "price_rejections.json"
    rejection_path.write_text(
        json.dumps(
            price_failures,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    kap_manifest = {
        "contract": "PROSPECTIVE_KAP_CA_GAP_CAPTURE_V1",
        "source_url": KAP_URL,
        "captured_at": captured_at.isoformat(),
        "window_start": CA_START.isoformat(),
        "window_end": local_date.isoformat(),
        "windows": kap_manifest_rows,
        "complete": True,
        "window_count": len(kap_manifest_rows),
        "total_rows": sum(row["row_count"] for row in kap_manifest_rows),
        "total_ca_rows": sum(
            row["ca_row_count"] for row in kap_manifest_rows
        ),
    }
    kap_manifest_path = OUT / "kap_capture_manifest.json"
    kap_manifest_path.write_text(
        json.dumps(
            kap_manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    status_counts = {
        str(key): int(value)
        for key, value in gate["status"].value_counts().sort_index().items()
    }
    provenance = {
        "contract": "PROSPECTIVE_HIGH52_INPUT_CA_RISK_CAPTURE_V1",
        "activation_at": ACTIVATION.isoformat(),
        "captured_at": captured_at.isoformat(),
        "capture_local_date": local_date.isoformat(),
        "real_shadow_run_created": False,
        "production_ready": False,
        "price_history": {
            "requested_tickers": len(tickers),
            "captured_tickers": int(price_history["ticker"].nunique()),
            "captured_rows": int(len(price_history)),
            "rejection_count": len(price_failures),
            "tickers_with_252_adj_close": int(
                (gate["finite_positive_adj_close_observations"] >= 252).sum()
            ),
            "price_history_gzip_sha256": price_sha,
            "auto_adjust": False,
        },
        "recent_ca_gap": {
            "start": CA_START.isoformat(),
            "end": local_date.isoformat(),
            "coverage_complete": True,
            "window_count": len(kap_manifest_rows),
            "market_wide_rows": kap_manifest["total_rows"],
            "market_wide_ca_rows": kap_manifest["total_ca_rows"],
            "current_universe_risk_rows": int(len(risk_frame)),
            "current_universe_tickers_with_risk": int(
                len(
                    set(risk_frame["ticker"])
                    if not risk_frame.empty
                    else set()
                )
            ),
        },
        "ticker_gate": {
            "status_counts": status_counts,
            "score_computation_allowed": int(
                gate["score_computation_allowed"].sum()
            ),
            "shadow_signal_allowed": int(gate["shadow_signal_allowed"].sum()),
            "historical_ca_reconciliation_complete": False,
        },
        "limitations": [
            "Yahoo adjusted close is validated live research evidence, not official Borsa total-return truth.",
            "Recent KAP subject/summary classification identifies risk disclosures but does not invent ex-date, ratio, payment date, or cash amount.",
            "Corporate actions in the older portion of the 252-day window remain to be reconciled against the frozen historical KAP inventory.",
            "No live factor score or shadow signal is emitted."
        ],
    }
    provenance_path = OUT / "provenance.json"
    provenance_path.write_text(
        json.dumps(
            provenance,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    files = [
        price_path,
        risk_path,
        gate_path,
        rejection_path,
        kap_manifest_path,
        provenance_path,
    ]
    for path in kap_dir.glob("*"):
        files.append(path)

    sums = [
        f"{sha256_bytes(path.read_bytes())}  {path.relative_to(OUT)}"
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
