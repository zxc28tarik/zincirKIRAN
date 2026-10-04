"""Historical market bootstrap from validated cross-project evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MarketBootstrapAuthority(StrEnum):
    VALIDATED_DERIVED_MARKET_DATA = "VALIDATED_DERIVED_MARKET_DATA"
    VALIDATED_EXECUTION_PANEL = "VALIDATED_EXECUTION_PANEL"
    OFFICIAL_BORSA_EVIDENCE = "OFFICIAL_BORSA_EVIDENCE"


@dataclass(frozen=True)
class HistoricalMarketArtifact:
    artifact_id: str
    source_repository: str
    source_commit: str
    source_path: str
    sha256: str
    authority: MarketBootstrapAuthority
    row_count: int | None
    coverage_start: str | None
    coverage_end: str | None
    scope_note: str

    def __post_init__(self) -> None:
        for name, value in (
            ("artifact_id", self.artifact_id),
            ("source_repository", self.source_repository),
            ("source_commit", self.source_commit),
            ("source_path", self.source_path),
            ("sha256", self.sha256),
            ("scope_note", self.scope_note),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if len(self.source_commit) != 40:
            raise ValueError("source_commit must be full SHA")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be 64 hex chars")
        int(self.source_commit, 16)
        int(self.sha256, 16)
        if self.row_count is not None and self.row_count <= 0:
            raise ValueError("row_count must be positive when supplied")


def default_market_bootstrap_artifacts() -> tuple[HistoricalMarketArtifact, ...]:
    repo = "zxc28tarik/TOTAL-RASYO-HESAPLAYICI"
    commit = "883e680a2564e38f4c08a21bc88aa95b8f164036"
    artifacts = (
        HistoricalMarketArtifact(
            artifact_id="v24-daily-member-prices",
            source_repository=repo,
            source_commit=commit,
            source_path="data/backtest_sources/yahoo_resolved/historical_member_prices_resolved_2020-07_2026-08.csv.gz",
            sha256="b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141",
            authority=MarketBootstrapAuthority.VALIDATED_DERIVED_MARKET_DATA,
            row_count=271267,
            coverage_start="2020-07",
            coverage_end="2026-08",
            scope_note=(
                "Yahoo-derived daily stock-price corpus with official Borsa ticker-lineage "
                "resolution; no date shifting or forward fill. Not official Borsa market data."
            ),
        ),
        HistoricalMarketArtifact(
            artifact_id="v24-monthly-execution-panel",
            source_repository=repo,
            source_commit=commit,
            source_path="data/backtest_sources/yahoo_resolved/monthly_member_signal_price_coverage.csv",
            sha256="a3b14014aa4d3ff16a082bc0dac64346b906f4b7720aeae5a8c449a2add314f2",
            authority=MarketBootstrapAuthority.VALIDATED_EXECUTION_PANEL,
            row_count=6000,
            coverage_start="2021-08",
            coverage_end="2026-07",
            scope_note=(
                "Exact 60x100 BIST100 monthly signal-day open/close panel; 5988 Yahoo/lineage "
                "rows plus 12 official Borsa THB supplements."
            ),
        ),
    )
    return tuple(sorted(artifacts, key=lambda item: item.artifact_id))


def can_label_official_borsa(artifact: HistoricalMarketArtifact) -> bool:
    return artifact.authority is MarketBootstrapAuthority.OFFICIAL_BORSA_EVIDENCE


def require_official_borsa(artifact: HistoricalMarketArtifact) -> None:
    if not can_label_official_borsa(artifact):
        raise ValueError("artifact is not authorized to be labeled official Borsa evidence")
