"""Experimental semantic financial-fact bootstrap.

These artifacts come from real KAP bulk archives and deterministic semantic
materialization, but historical superseded-version enumeration is incomplete.
They are therefore research-only and can never be silently promoted to
authoritative PIT evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SemanticFactAuthority(StrEnum):
    EXPERIMENTAL_VERSION_RISK = "EXPERIMENTAL_VERSION_RISK"


@dataclass(frozen=True)
class ExperimentalSemanticArtifact:
    artifact_id: str
    source_repository: str
    source_commit: str
    source_path: str
    sha256: str
    report_count: int
    fact_count: int
    authority: SemanticFactAuthority
    risk_ids: tuple[str, ...]
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
            raise ValueError("source_commit must be a full SHA")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be 64 hex chars")
        int(self.source_commit, 16)
        int(self.sha256, 16)
        if self.report_count <= 0 or self.fact_count <= 0:
            raise ValueError("report_count and fact_count must be positive")
        if not self.risk_ids:
            raise ValueError("experimental semantic artifact requires risk_ids")
        if self.risk_ids != tuple(sorted(set(self.risk_ids))):
            raise ValueError("risk_ids must be unique and sorted")


@dataclass(frozen=True)
class ExperimentalSemanticCorpus:
    corpus_id: str
    artifacts: tuple[ExperimentalSemanticArtifact, ...]
    total_report_count: int
    total_fact_count: int
    own_period_visible_cells: int
    historical_cells: int
    authoritative_claim_allowed: bool = False

    def __post_init__(self) -> None:
        if not self.corpus_id.strip():
            raise ValueError("corpus_id is required")
        if self.authoritative_claim_allowed:
            raise ValueError("experimental semantic corpus cannot authorize PIT claims")
        if self.artifacts != tuple(sorted(self.artifacts, key=lambda item: item.artifact_id)):
            raise ValueError("artifacts must be deterministically sorted")
        if sum(item.report_count for item in self.artifacts) != self.total_report_count:
            raise ValueError("total_report_count does not match artifacts")
        if sum(item.fact_count for item in self.artifacts) != self.total_fact_count:
            raise ValueError("total_fact_count does not match artifacts")
        if not 0 <= self.own_period_visible_cells <= self.historical_cells:
            raise ValueError("own_period_visible_cells must be within historical cell count")


RISK_IDS = tuple(
    sorted(
        (
            "ORIGINAL_CATALOG_BYTES_UNAVAILABLE",
            "SUPERSEDED_HISTORICAL_KAP_REPORT_VERSIONS_NOT_ENUMERATED",
        )
    )
)


def total_rasyo_experimental_semantic_corpus() -> ExperimentalSemanticCorpus:
    repo = "zxc28tarik/TOTAL-RASYO-HESAPLAYICI"
    commit = "c8b481e79e270f2c095e8c180671a3f483f0775e"
    artifacts = (
        ExperimentalSemanticArtifact(
            artifact_id="semantic-primary",
            source_repository=repo,
            source_commit=commit,
            source_path=(
                "data/backtest_sources/experimental_semantic_facts_v1/"
                "semantic_reports.jsonl.gz"
            ),
            sha256="07863ddbd78924ad276e7d0aeba7fa6eec9733477b4ca3c02ece285bcf1d9e7a",
            report_count=4581,
            fact_count=195782,
            authority=SemanticFactAuthority.EXPERIMENTAL_VERSION_RISK,
            risk_ids=RISK_IDS,
            scope_note=(
                "Primary deterministic semantic materialization from real KAP bulk "
                "archives. Version enumeration is incomplete."
            ),
        ),
        ExperimentalSemanticArtifact(
            artifact_id="semantic-alias-supplement",
            source_repository=repo,
            source_commit=commit,
            source_path=(
                "data/backtest_sources/experimental_semantic_facts_v1/"
                "semantic_alias_reports.jsonl.gz"
            ),
            sha256="adb49330f29b370306d69545db1a48d34a5fda6d763a4d4bdfd2eadc56df06a3",
            report_count=3,
            fact_count=136,
            authority=SemanticFactAuthority.EXPERIMENTAL_VERSION_RISK,
            risk_ids=RISK_IDS,
            scope_note="Predecessor-ticker semantic supplement; experimental only.",
        ),
        ExperimentalSemanticArtifact(
            artifact_id="semantic-entity-supplement",
            source_repository=repo,
            source_commit=commit,
            source_path=(
                "data/backtest_sources/experimental_semantic_facts_v1/"
                "semantic_entity_reports.jsonl.gz"
            ),
            sha256="d70e8a1056fd16b03a9ba44c8d6d3c183cb9e2f3604f45692d90817e5b52d741",
            report_count=468,
            fact_count=4051,
            authority=SemanticFactAuthority.EXPERIMENTAL_VERSION_RISK,
            risk_ids=RISK_IDS,
            scope_note=(
                "Archived multi-code financial-entity supplement; share/price basis "
                "is not proven by this artifact."
            ),
        ),
    )
    return ExperimentalSemanticCorpus(
        corpus_id="total-rasyo-experimental-semantic-facts-v1",
        artifacts=tuple(sorted(artifacts, key=lambda item: item.artifact_id)),
        total_report_count=5052,
        total_fact_count=199969,
        own_period_visible_cells=5633,
        historical_cells=6000,
        authoritative_claim_allowed=False,
    )


def allow_factor_lab_experiment(
    corpus: ExperimentalSemanticCorpus,
    *,
    experiment_authority: str,
) -> None:
    if experiment_authority != "EXPERIMENTAL_VERSION_RISK":
        raise ValueError(
            "experimental semantic facts require EXPERIMENTAL_VERSION_RISK experiment"
        )
    if corpus.authoritative_claim_allowed:
        raise ValueError("experimental corpus authority invariant violated")


def require_authoritative_use(_: ExperimentalSemanticCorpus) -> None:
    raise ValueError(
        "experimental semantic facts are not authorized for authoritative PIT, "
        "shadow, tournament champion promotion, or production evidence"
    )


PROHIBITED_SOURCE_OUTPUTS = tuple(
    sorted(
        (
            "TOTAL_RASYO_P4_SCORE",
            "TOTAL_RASYO_RANKING",
            "TOTAL_RASYO_DECISION",
        )
    )
)
