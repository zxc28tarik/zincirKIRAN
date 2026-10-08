"""Fail-closed extraction for the locked share-multiplier contract."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping

from zincir_kiran.corporate_action_economic_resolution import (
    ShareMultiplierContractEvidence,
    ShareMultiplierContractResult,
    evaluate_share_multiplier_contract,
)

_DATE_RE = re.compile(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b")
_PERCENT_RE = re.compile(r"(?<!\d)(\d[\d.]*?(?:,\d+)?)\s*%")
_NUMBER_RE = re.compile(r"(?<!\d)(\d[\d.]*?(?:,\d+)?)(?!\d)")

_PROVISIONAL_WORDS = (
    "ONGORULEN",
    "TAHMINI",
    "PLANLANAN",
    "TEKLIF",
    "TASLAK",
)

_EFFECTIVE_DATE_LABELS = (
    "HAK KULLANIM TARIHI",
    "PAY ALMA HAKKI KULLANIM TARIHI",
    "BEDELSIZ PAY ALMA HAKKI KULLANIM TARIHI",
)

_BONUS_RATE_LABELS = (
    "BEDELSIZ PAY ALMA ORANI",
    "BEDELSIZ ORANI",
)

_TARGET_CONTEXT_WORDS = (
    "PAY",
    "GRUP",
    "BORSA",
    "ISIN",
)


@dataclass(frozen=True)
class ShareMultiplierExtraction:
    evidence: ShareMultiplierContractEvidence
    contract: ShareMultiplierContractResult
    extraction_reason_codes: tuple[str, ...]
    matched_target_rows: int
    effective_date_candidates: tuple[str, ...]
    bonus_rate_candidates: tuple[float, ...]


def _ascii_upper(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).upper()


def _parse_tr_number(value: str) -> float:
    value = value.strip()
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    return float(value)


def _normalize_date(value: str) -> str:
    parsed = datetime.strptime(value.replace("/", ".").replace("-", "."), "%d.%m.%Y")
    return parsed.date().isoformat()


def _group_rows(cells: Iterable[Mapping[str, object]]) -> list[list[str]]:
    grouped: dict[tuple[int, int], list[tuple[int, str]]] = {}
    for cell in cells:
        table_index = int(cell["table_index"])
        row_index = int(cell["row_index"])
        cell_index = int(cell["cell_index"])
        text = str(cell.get("cell_text") or "").strip()
        if not text:
            continue
        grouped.setdefault((table_index, row_index), []).append((cell_index, text))
    rows: list[list[str]] = []
    for key in sorted(grouped):
        ordered = [text for _, text in sorted(grouped[key])]
        rows.append(ordered)
    return rows


def extract_share_multiplier_contract(
    cells: Iterable[Mapping[str, object]],
    *,
    ticker: str,
) -> ShareMultiplierExtraction:
    """Extract only explicit official table evidence.

    The extractor deliberately prefers false negatives over inferred economics.
    It never uses vendor data and never derives a bonus rate from capital amounts.
    """

    ticker_norm = _ascii_upper(ticker.strip())
    rows = _group_rows(cells)
    extraction_reasons: list[str] = []

    target_rows = []
    effective_dates: set[str] = set()
    provisional_date_seen = False
    bonus_rates: set[float] = set()

    for row in rows:
        joined = " | ".join(row)
        normalized = _ascii_upper(joined)

        ticker_token = re.search(
            rf"(?<![A-Z0-9]){re.escape(ticker_norm)}(?![A-Z0-9])",
            normalized,
        )
        if ticker_token and any(word in normalized for word in _TARGET_CONTEXT_WORDS):
            target_rows.append(joined)

        if any(label in normalized for label in _EFFECTIVE_DATE_LABELS):
            row_dates = []
            for match in _DATE_RE.finditer(joined):
                try:
                    row_dates.append(_normalize_date(match.group(1)))
                except ValueError:
                    extraction_reasons.append("INVALID_EFFECTIVE_DATE_VALUE")
            if any(word in normalized for word in _PROVISIONAL_WORDS):
                provisional_date_seen = True
            else:
                effective_dates.update(row_dates)

        if any(label in normalized for label in _BONUS_RATE_LABELS):
            values: list[float] = []
            for match in _PERCENT_RE.finditer(joined):
                try:
                    values.append(_parse_tr_number(match.group(1)))
                except ValueError:
                    extraction_reasons.append("INVALID_BONUS_RATE_VALUE")
            if not values:
                # KAP tables may carry the (%) marker in the label and the
                # numeric value in a later cell. Only inspect cells after the
                # label-bearing cell and never infer from unrelated capital rows.
                label_index = next(
                    (
                        idx
                        for idx, text in enumerate(row)
                        if any(
                            label in _ascii_upper(text)
                            for label in _BONUS_RATE_LABELS
                        )
                    ),
                    None,
                )
                if label_index is not None:
                    for text in row[label_index + 1 :]:
                        for match in _NUMBER_RE.finditer(text):
                            try:
                                values.append(_parse_tr_number(match.group(1)))
                            except ValueError:
                                extraction_reasons.append("INVALID_BONUS_RATE_VALUE")
            bonus_rates.update(value for value in values if value > 0)

    exact_target = len(target_rows) == 1
    if len(target_rows) > 1:
        extraction_reasons.append("AMBIGUOUS_TARGET_SHARE_GROUP")
    elif len(target_rows) == 0:
        extraction_reasons.append("TARGET_SHARE_GROUP_NOT_FOUND")

    effective_date: str | None = None
    effective_finalized = False
    if len(effective_dates) == 1:
        effective_date = next(iter(effective_dates))
        effective_finalized = True
    elif len(effective_dates) > 1:
        extraction_reasons.append("AMBIGUOUS_EFFECTIVE_DATE")
    elif provisional_date_seen:
        extraction_reasons.append("ONLY_PROVISIONAL_EFFECTIVE_DATE_FOUND")
    else:
        extraction_reasons.append("FINAL_EFFECTIVE_DATE_NOT_FOUND")

    bonus_rate: float | None = None
    if len(bonus_rates) == 1:
        bonus_rate = next(iter(bonus_rates))
    elif len(bonus_rates) > 1:
        extraction_reasons.append("AMBIGUOUS_BONUS_RATE")
    else:
        extraction_reasons.append("POSITIVE_BONUS_RATE_NOT_FOUND")

    evidence = ShareMultiplierContractEvidence(
        exact_listed_ticker_share_group_once=exact_target,
        effective_date=effective_date,
        effective_date_finalized=effective_finalized,
        share_multiplier=None,
        bonus_rate_percent=bonus_rate,
    )
    contract = evaluate_share_multiplier_contract(evidence)
    return ShareMultiplierExtraction(
        evidence=evidence,
        contract=contract,
        extraction_reason_codes=tuple(sorted(set(extraction_reasons))),
        matched_target_rows=len(target_rows),
        effective_date_candidates=tuple(sorted(effective_dates)),
        bonus_rate_candidates=tuple(sorted(bonus_rates)),
    )
