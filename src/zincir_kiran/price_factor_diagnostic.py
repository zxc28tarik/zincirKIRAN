"""Contracts for the first real price-factor diagnostic."""

from __future__ import annotations

from dataclasses import dataclass


FACTORS = (
    "HIGH_52W_PROXIMITY",
    "LIQUIDITY_63D",
    "LOW_VOL_63D",
    "MOM_12_1",
    "MOM_6_1",
)
HORIZONS = (20, 60, 120, 252)


@dataclass(frozen=True)
class PriceFactorDiagnosticSpec:
    factors: tuple[str, ...] = FACTORS
    horizons: tuple[int, ...] = HORIZONS
    target_authority: str = "DIAGNOSTIC_RETURN_PROXY"
    production_ready: bool = False

    def __post_init__(self) -> None:
        if self.factors != tuple(sorted(set(self.factors))):
            raise ValueError("factors must be unique and sorted")
        if self.horizons != tuple(sorted(set(self.horizons))):
            raise ValueError("horizons must be unique and sorted")
        if self.target_authority != "DIAGNOSTIC_RETURN_PROXY":
            raise ValueError("first real price lab target authority is diagnostic only")
        if self.production_ready:
            raise ValueError("diagnostic price factor lab cannot be production-ready")
