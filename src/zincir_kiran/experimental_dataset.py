"""Experimental Factor-Lab dataset assembly primitives.

The dataset combines validated historical market evidence with real KAP-derived
semantic financial facts. Because financial superseded-version enumeration is
incomplete, the assembled dataset remains EXPERIMENTAL_VERSION_RISK.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from .baselines import Horizon


class ResearchDatasetAuthority(StrEnum):
    EXPERIMENTAL_VERSION_RISK = "EXPERIMENTAL_VERSION_RISK"


@dataclass(frozen=True)
class DatasetInputArtifact:
    artifact_id: str
    sha256: str
    authority: str
    scope_note: str

    def __post_init__(self) -> None:
        if not self.artifact_id.strip() or not self.authority.strip() or not self.scope_note.strip():
            raise ValueError("dataset input identity/authority/scope is required")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be 64 hex chars")
        int(self.sha256, 16)


@dataclass(frozen=True)
class ExperimentalFactorDatasetManifest:
    dataset_id: str
    authority: ResearchDatasetAuthority
    inputs: tuple[DatasetInputArtifact, ...]
    historical_cells: int
    cells_with_visible_financial_facts: int
    risk_ids: tuple[str, ...]
    production_eligible: bool = False

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id is required")
        if self.production_eligible:
            raise ValueError("experimental dataset cannot be production eligible")
        if self.inputs != tuple(sorted(self.inputs, key=lambda item: item.artifact_id)):
            raise ValueError("inputs must be deterministically sorted")
        if not 0 <= self.cells_with_visible_financial_facts <= self.historical_cells:
            raise ValueError("financial coverage must be within historical cell count")
        if self.risk_ids != tuple(sorted(set(self.risk_ids))):
            raise ValueError("risk_ids must be unique and sorted")


def default_experimental_factor_dataset_manifest() -> ExperimentalFactorDatasetManifest:
    inputs = (
        DatasetInputArtifact(
            artifact_id="historical-member-market",
            sha256="b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141",
            authority="VALIDATED_DERIVED_MARKET_DATA",
            scope_note="271267 historical member OHLC/Adj Close/Volume rows.",
        ),
        DatasetInputArtifact(
            artifact_id="historical-sector-routes",
            sha256="f0c28c7babd018eb8994afdf4911a9d338dad43b291a1084a7acc47a3919c478",
            authority="CANONICAL_PIT",
            scope_note="209 tickers / 210 historical sector-route rows.",
        ),
        DatasetInputArtifact(
            artifact_id="index-closes",
            sha256="32a740f7a7114e03c885d1ae75c8bacd081b5254b043521fd76ca5f8e34e786e",
            authority="CANONICAL_PIT",
            scope_note="7415 official XU100 and broad-sector index closes.",
        ),
        DatasetInputArtifact(
            artifact_id="semantic-financial-primary",
            sha256="07863ddbd78924ad276e7d0aeba7fa6eec9733477b4ca3c02ece285bcf1d9e7a",
            authority="EXPERIMENTAL_VERSION_RISK",
            scope_note="4581 reports / 195782 primary semantic financial facts.",
        ),
        DatasetInputArtifact(
            artifact_id="semantic-financial-alias",
            sha256="adb49330f29b370306d69545db1a48d34a5fda6d763a4d4bdfd2eadc56df06a3",
            authority="EXPERIMENTAL_VERSION_RISK",
            scope_note="Predecessor ticker semantic supplement.",
        ),
        DatasetInputArtifact(
            artifact_id="semantic-financial-entity",
            sha256="d70e8a1056fd16b03a9ba44c8d6d3c183cb9e2f3604f45692d90817e5b52d741",
            authority="EXPERIMENTAL_VERSION_RISK",
            scope_note="Multi-code financial entity semantic supplement.",
        ),
    )
    return ExperimentalFactorDatasetManifest(
        dataset_id="zk-experimental-factor-lab-v1",
        authority=ResearchDatasetAuthority.EXPERIMENTAL_VERSION_RISK,
        inputs=tuple(sorted(inputs, key=lambda item: item.artifact_id)),
        historical_cells=6000,
        cells_with_visible_financial_facts=5633,
        risk_ids=tuple(
            sorted(
                (
                    "ORIGINAL_CATALOG_BYTES_UNAVAILABLE",
                    "SUPERSEDED_HISTORICAL_KAP_REPORT_VERSIONS_NOT_ENUMERATED",
                )
            )
        ),
        production_eligible=False,
    )


@dataclass(frozen=True)
class MarketPoint:
    security_id: str
    trade_date: date
    close: float

    def __post_init__(self) -> None:
        if not self.security_id.strip():
            raise ValueError("security_id is required")
        if not math.isfinite(self.close) or self.close <= 0:
            raise ValueError("close must be positive and finite")


@dataclass(frozen=True)
class ForwardExcessLabel:
    security_id: str
    signal_date: date
    horizon: Horizon
    future_date: date
    stock_return: float
    market_return: float
    excess_return: float


def forward_excess_label(
    *,
    security_id: str,
    signal_date: date,
    horizon: Horizon,
    trading_dates: tuple[date, ...],
    stock_closes: dict[date, float],
    market_closes: dict[date, float],
) -> ForwardExcessLabel | None:
    """Compute exact trading-day market-relative return.

    The signal date and future date must both exist on the supplied trading
    calendar. A horizon that has not matured returns None; it is never zero-filled.
    """
    if trading_dates != tuple(sorted(set(trading_dates))):
        raise ValueError("trading_dates must be unique and sorted")
    try:
        start_index = trading_dates.index(signal_date)
    except ValueError as exc:
        raise ValueError("signal_date is not on trading calendar") from exc

    future_index = start_index + horizon.value
    if future_index >= len(trading_dates):
        return None
    future_date = trading_dates[future_index]

    required = (
        ("stock start", stock_closes.get(signal_date)),
        ("stock future", stock_closes.get(future_date)),
        ("market start", market_closes.get(signal_date)),
        ("market future", market_closes.get(future_date)),
    )
    if any(value is None for _, value in required):
        return None
    for name, value in required:
        assert value is not None
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} close must be positive and finite")

    stock_start = float(stock_closes[signal_date])
    stock_future = float(stock_closes[future_date])
    market_start = float(market_closes[signal_date])
    market_future = float(market_closes[future_date])
    stock_return = stock_future / stock_start - 1.0
    market_return = market_future / market_start - 1.0
    return ForwardExcessLabel(
        security_id=security_id,
        signal_date=signal_date,
        horizon=horizon,
        future_date=future_date,
        stock_return=stock_return,
        market_return=market_return,
        excess_return=stock_return - market_return,
    )


def require_experimental_factor_lab_use(
    manifest: ExperimentalFactorDatasetManifest,
    *,
    requested_authority: str,
) -> None:
    if requested_authority != ResearchDatasetAuthority.EXPERIMENTAL_VERSION_RISK.value:
        raise ValueError("experimental dataset cannot be promoted to authoritative research")
    if manifest.production_eligible:
        raise ValueError("experimental dataset production invariant violated")
