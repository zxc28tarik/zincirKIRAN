#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "research/preregistrations/first_post_activation_live_snapshot_v1.json"
CATALOG = ROOT / "research/source_catalogs/current_bist100_q4_2026_v1.json"
OUT = ROOT / "data/live_shadow/first_post_activation_live_snapshot_v1"

ACTIVATION = datetime.fromisoformat("2026-10-07T22:10:15+00:00")
ANNOUNCEMENT_URL = (
    "https://www.borsaistanbul.com/duyuru/15598/"
    "bist-pay-endeksleri-donemsel-degisiklikleri"
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_bytes(url: str, *, attempts: int = 4) -> bytes:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "zincir-kiran-shadow-snapshot/1.0",
                    "Accept": "*/*",
                },
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except Exception as exc:
            last = exc
            time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}") from last


def load_anchor(prereg: dict) -> tuple[list[str], str]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    anchor = catalog["anchor"]
    expected = prereg["universe"]["baseline"]["sha256"]
    if anchor["source_sha256"] != expected:
        raise RuntimeError("source catalog anchor SHA does not match preregistration")
    tickers = sorted(set(str(x).strip().upper() for x in anchor["members"]))
    if len(tickers) != 100:
        raise RuntimeError(f"expected 100 July anchor tickers, found {len(tickers)}")
    if catalog["q4_event"]["adds"] != prereg["universe"]["q4_event"]["adds"]:
        raise RuntimeError("source catalog Q4 additions drifted from preregistration")
    if catalog["q4_event"]["removes"] != prereg["universe"]["q4_event"]["removes"]:
        raise RuntimeError("source catalog Q4 removals drifted from preregistration")
    return tickers, anchor["source_sha256"]


def capture_announcement(prereg: dict) -> tuple[bytes, str]:
    payload = fetch_bytes(ANNOUNCEMENT_URL)
    if not payload:
        raise RuntimeError("official announcement payload is empty")
    text = payload.decode("utf-8", errors="ignore").upper()
    event = prereg["universe"]["q4_event"]
    missing_tokens = [
        ticker
        for ticker in list(event["adds"]) + list(event["removes"])
        if ticker.upper() not in text
    ]
    if missing_tokens:
        raise RuntimeError(
            "official Q4 announcement missing expected tickers: "
            + ",".join(sorted(missing_tokens))
        )
    return payload, sha256_bytes(payload)


def reconstruct_universe(prereg: dict, anchor: list[str]) -> list[str]:
    event = prereg["universe"]["q4_event"]
    adds = [str(x).strip().upper() for x in event["adds"]]
    removes = [str(x).strip().upper() for x in event["removes"]]
    if len(adds) != 27 or len(removes) != 27:
        raise RuntimeError("Q4 event must contain exactly 27 additions/removals")
    if len(set(adds)) != len(adds) or len(set(removes)) != len(removes):
        raise RuntimeError("Q4 event contains duplicate ticker")
    current = set(anchor)
    missing_removes = sorted(set(removes) - current)
    existing_adds = sorted(set(adds) & current)
    if missing_removes or existing_adds:
        raise RuntimeError(
            f"Q4 event precondition failed missing_removes={missing_removes} "
            f"existing_adds={existing_adds}"
        )
    current.difference_update(removes)
    current.update(adds)
    if len(current) != 100:
        raise RuntimeError(f"current BIST100 size is {len(current)}, expected 100")
    return sorted(current)


def _extract_latest(
    frame: pd.DataFrame,
    ticker: str,
    *,
    cutoff_date,
) -> dict | None:
    symbol = f"{ticker}.IS"
    if (
        frame.empty
        or not isinstance(frame.columns, pd.MultiIndex)
        or symbol not in frame.columns.get_level_values(0)
    ):
        return None
    rows = frame[symbol].copy()
    dates = pd.to_datetime(rows.index, errors="coerce")
    rows = rows.loc[dates.date <= cutoff_date]
    close = pd.to_numeric(rows.get("Close"), errors="coerce")
    rows = rows.loc[close.notna()]
    if rows.empty:
        return None
    row = rows.iloc[-1]
    trade_date = pd.Timestamp(rows.index[-1]).date().isoformat()
    raw_close = float(row["Close"])
    volume = float(row["Volume"]) if pd.notna(row.get("Volume")) else float("nan")
    if not (raw_close > 0):
        return None
    if not (volume >= 0):
        return None
    return {
        "ticker": ticker,
        "source_symbol": symbol,
        "trade_date": trade_date,
        "raw_close": raw_close,
        "volume": volume,
        "auto_adjust": False,
        "price_field": "Close",
        "volume_field": "Volume",
    }


def capture_market(tickers: list[str], *, captured_at: datetime) -> tuple[pd.DataFrame, list[dict]]:
    cutoff = captured_at.astimezone(ZoneInfo("Europe/Istanbul")).date()
    rows: list[dict] = []
    failures: list[dict] = []
    chunk_size = 50
    for offset in range(0, len(tickers), chunk_size):
        batch = tickers[offset : offset + chunk_size]
        symbols = [f"{ticker}.IS" for ticker in batch]
        try:
            frame = yf.download(
                symbols,
                period="10d",
                auto_adjust=False,
                actions=True,
                repair=False,
                progress=False,
                threads=True,
                group_by="ticker",
            )
        except Exception as exc:
            failures.extend(
                {"ticker": ticker, "reason": type(exc).__name__}
                for ticker in batch
            )
            continue
        for ticker in batch:
            result = _extract_latest(frame, ticker, cutoff_date=cutoff)
            if result is None:
                failures.append(
                    {"ticker": ticker, "reason": "RAW_CLOSE_OR_VOLUME_NOT_RETURNED"}
                )
            else:
                rows.append(result)
    market = pd.DataFrame(rows)
    if not market.empty:
        market = market.sort_values("ticker").reset_index(drop=True)
    return market, sorted(failures, key=lambda row: row["ticker"])


def write_gzip(path: Path, payload: bytes) -> str:
    zipped = gzip.compress(payload, compresslevel=9, mtime=0)
    path.write_bytes(zipped)
    return sha256_bytes(zipped)


def main() -> int:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    captured_at = datetime.now(UTC)
    if captured_at <= ACTIVATION:
        raise RuntimeError("capture must occur strictly after Shadow v1 activation")

    OUT.mkdir(parents=True, exist_ok=True)
    anchor, anchor_sha = load_anchor(prereg)
    announcement_bytes, announcement_raw_sha = capture_announcement(prereg)
    universe = reconstruct_universe(prereg, anchor)

    universe_frame = pd.DataFrame(
        {
            "ticker": universe,
            "index_code": "XU100",
            "effective_period_start": "2026-10-01",
            "effective_period_end": "2026-12-31",
        }
    )
    universe_path = OUT / "universe.csv"
    universe_frame.to_csv(universe_path, index=False, lineterminator="\n")

    announcement_path = OUT / "official_q4_announcement.html.gz"
    announcement_gzip_sha = write_gzip(announcement_path, announcement_bytes)

    market, failures = capture_market(universe, captured_at=captured_at)
    market_path = OUT / "market.csv.gz"
    market_csv = market.to_csv(index=False, lineterminator="\n").encode("utf-8")
    market_sha = write_gzip(market_path, market_csv)

    rejection_path = OUT / "rejections.json"
    rejection_path.write_text(
        json.dumps(failures, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    universe_sha = sha256_bytes(universe_path.read_bytes())
    rejection_sha = sha256_bytes(rejection_path.read_bytes())

    latest_trade_dates = sorted(set(market.get("trade_date", pd.Series(dtype=str)).astype(str)))
    provenance = {
        "contract": "FIRST_POST_ACTIVATION_LIVE_SNAPSHOT_V1",
        "shadow_protocol_id": prereg["shadow_protocol_id"],
        "activation_at": prereg["activation_at"],
        "captured_at": captured_at.isoformat(),
        "production_ready": False,
        "real_shadow_run_created": False,
        "capture_once_then_verify": True,
        "universe": {
            "authority": "VALIDATED_LIVE_RESEARCH",
            "member_count": len(universe),
            "baseline_sha256": anchor_sha,
            "official_q4_source_url": ANNOUNCEMENT_URL,
            "official_q4_raw_sha256": announcement_raw_sha,
            "official_q4_gzip_sha256": announcement_gzip_sha,
            "universe_csv_sha256": universe_sha,
        },
        "market": {
            "authority": "VALIDATED_LIVE_RESEARCH",
            "requested_tickers": len(universe),
            "captured_rows": int(len(market)),
            "rejection_count": len(failures),
            "trade_dates": latest_trade_dates,
            "market_gzip_sha256": market_sha,
            "rejections_sha256": rejection_sha,
            "auto_adjust": False,
        },
        "snapshot_domains_present": [
            "UNIVERSE",
            "MARKET_PRICES",
            "VOLUME_LIQUIDITY",
        ],
        "snapshot_domains_missing": [
            "CORPORATE_ACTIONS",
            "FINANCIALS",
            "PUBLICATION_REVISIONS",
            "SECTOR_ROUTES",
            "TRAIN_EVIDENCE_STATE",
            "TRAINED_MODEL_STATE",
        ],
        "limitations": [
            "Universe is a validated live research reconstruction from a frozen Q3 anchor plus the official Q4 periodic event, not a direct full constituent export.",
            "Market prices and volume are Yahoo-derived validated live research evidence, not official Borsa market data.",
            "No corporate-action, financial revision, model-state or train-evidence live snapshot is captured in this implementation.",
            "No shadow run is created."
        ],
    }
    provenance_path = OUT / "provenance.json"
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    sums = []
    for path in sorted(
        [
            announcement_path,
            universe_path,
            market_path,
            rejection_path,
            provenance_path,
        ],
        key=lambda item: item.name,
    ):
        sums.append(f"{sha256_bytes(path.read_bytes())}  {path.name}")
    (OUT / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")

    print(json.dumps(provenance, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
