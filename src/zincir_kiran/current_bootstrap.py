"""Current BIST roster/share-state bootstrap from validated Total Rasyo evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CurrentEvidenceAuthority(StrEnum):
    CURRENT_ROSTER_DISCOVERY_ONLY = "CURRENT_ROSTER_DISCOVERY_ONLY"
    CURRENT_SHARE_STATE_EVIDENCE = "CURRENT_SHARE_STATE_EVIDENCE"
    CURRENT_MARKET_SNAPSHOT = "CURRENT_MARKET_SNAPSHOT"


@dataclass(frozen=True)
class CurrentBootstrapArtifact:
    artifact_id: str
    source_repository: str
    source_commit: str
    source_path: str
    sha256: str
    authority: CurrentEvidenceAuthority
    row_count: int
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
        if len(self.source_commit) != 40 or len(self.sha256) != 64:
            raise ValueError("full commit and SHA256 are required")
        int(self.source_commit, 16)
        int(self.sha256, 16)
        if self.row_count <= 0:
            raise ValueError("row_count must be positive")


def current_bootstrap_artifacts() -> tuple[CurrentBootstrapArtifact, ...]:
    repo = "zxc28tarik/TOTAL-RASYO-HESAPLAYICI"
    commit = "d0c5ce25832dc94c138fc6141bba8fa8392cd00b"
    rows = (
        CurrentBootstrapArtifact(
            artifact_id="current-kap-bist-roster",
            source_repository=repo,
            source_commit=commit,
            source_path="data/live/current_total_rasyo_v1/universe.csv",
            sha256="d9c860f918a538bc6426bd45e5e91ae4eb60fef188fda3630eef7fa78b83e4a1",
            authority=CurrentEvidenceAuthority.CURRENT_ROSTER_DISCOVERY_ONLY,
            row_count=807,
            scope_note=(
                "KAP public BIST-company roster captured 2026-09-16. May include multiple "
                "instrument/ticker codes for one issuer; not a final investable universe."
            ),
        ),
        CurrentBootstrapArtifact(
            artifact_id="current-explicit-share-basis",
            source_repository=repo,
            source_commit=commit,
            source_path="data/live/current_share_basis_v1/ticker_share_basis.jsonl.gz",
            sha256="e4f3ec10d33d7213df4e22a495797d28d7283bec9e9d9edff66acd9b554ab890",
            authority=CurrentEvidenceAuthority.CURRENT_SHARE_STATE_EVIDENCE,
            row_count=528,
            scope_note=(
                "Usable single-ticker explicit share basis from class nominal values and "
                "explicit nominal value per share. Current-only evidence."
            ),
        ),
        CurrentBootstrapArtifact(
            artifact_id="current-raw-close",
            source_repository=repo,
            source_commit=commit,
            source_path="data/live/current_raw_close_v1/raw_close.csv.gz",
            sha256="ebd6a713728578d38ab15ad0888aaa0c7095243efb698691b3312e980d662765",
            authority=CurrentEvidenceAuthority.CURRENT_MARKET_SNAPSHOT,
            row_count=629,
            scope_note=(
                "Current Yahoo raw Close capture with auto_adjust=false; adjusted close is "
                "diagnostic only. Current snapshot, not historical PIT evidence."
            ),
        ),
    )
    return tuple(sorted(rows, key=lambda item: item.artifact_id))


def require_historical_use(_: CurrentBootstrapArtifact) -> None:
    raise ValueError("current bootstrap artifact cannot be used for historical backfill")
