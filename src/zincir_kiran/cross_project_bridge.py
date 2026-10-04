"""Cross-project evidence bridge for Zincir Kıran.

References evidence by exact repository, commit, path and hash. Reuse authority is
explicit; derived scores from the source project are never accepted as labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .evidence_phase import EvidenceDomain


class ReuseAuthority(StrEnum):
    CANONICAL_PIT = "CANONICAL_PIT"
    RAW_EVIDENCE_ONLY = "RAW_EVIDENCE_ONLY"
    POSITIVE_EVENT_ONLY = "POSITIVE_EVENT_ONLY"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    FORBIDDEN = "FORBIDDEN"


@dataclass(frozen=True)
class CrossRepoArtifactRef:
    source_repository: str
    source_commit: str
    source_path: str
    evidence_domain: EvidenceDomain
    expected_sha256: str | None
    authority: ReuseAuthority
    coverage_note: str
    source_pr: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("source_repository", self.source_repository),
            ("source_commit", self.source_commit),
            ("source_path", self.source_path),
            ("coverage_note", self.coverage_note),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if len(self.source_commit) != 40:
            raise ValueError("source_commit must be a full 40-char SHA")
        try:
            int(self.source_commit, 16)
        except ValueError as exc:
            raise ValueError("source_commit must be hexadecimal") from exc
        if self.expected_sha256 is not None:
            if len(self.expected_sha256) != 64:
                raise ValueError("expected_sha256 must be 64 hex characters")
            try:
                int(self.expected_sha256, 16)
            except ValueError as exc:
                raise ValueError("expected_sha256 must be hexadecimal") from exc


@dataclass(frozen=True)
class CrossProjectBootstrapManifest:
    manifest_id: str
    source_project: str
    artifacts: tuple[CrossRepoArtifactRef, ...]
    prohibited_source_products: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.manifest_id.strip() or not self.source_project.strip():
            raise ValueError("bootstrap manifest identity is required")
        if self.artifacts != tuple(
            sorted(
                self.artifacts,
                key=lambda item: (
                    item.evidence_domain.value,
                    item.source_commit,
                    item.source_path,
                ),
            )
        ):
            raise ValueError("artifacts must be deterministically sorted")
        if self.prohibited_source_products != tuple(
            sorted(set(self.prohibited_source_products))
        ):
            raise ValueError("prohibited_source_products must be unique and sorted")


def default_total_rasyo_bootstrap_manifest() -> CrossProjectBootstrapManifest:
    repo = "zxc28tarik/TOTAL-RASYO-HESAPLAYICI"
    artifacts = (
        CrossRepoArtifactRef(
            source_repository=repo,
            source_commit="445e9a7cb788124a52fd4ac171f3e16e6c67137e",
            source_path="data/backtest_sources/m3_source_package/index_closes.csv.gz",
            evidence_domain=EvidenceDomain.PRICES,
            expected_sha256="32a740f7a7114e03c885d1ae75c8bacd081b5254b043521fd76ca5f8e34e786e",
            authority=ReuseAuthority.CANONICAL_PIT,
            coverage_note=(
                "Official Borsa Istanbul XU100/XUSIN/XUHIZ/XUMAL/XUTEK closes; "
                "2020-07-27..2026-07-01; 7415 rows. Index/benchmark prices only, "
                "not single-stock execution prices."
            ),
            source_pr=15,
        ),
        CrossRepoArtifactRef(
            source_repository=repo,
            source_commit="445e9a7cb788124a52fd4ac171f3e16e6c67137e",
            source_path="data/backtest_sources/m3_source_package/sector_routes.csv.gz",
            evidence_domain=EvidenceDomain.UNIVERSE_HISTORY,
            expected_sha256="f0c28c7babd018eb8994afdf4911a9d338dad43b291a1084a7acc47a3919c478",
            authority=ReuseAuthority.CANONICAL_PIT,
            coverage_note=(
                "209 historical tickers / 210 half-open sector-route rows used across "
                "60 signal dates; includes GRTRK->GRTHO lineage evidence."
            ),
            source_pr=15,
        ),
        CrossRepoArtifactRef(
            source_repository=repo,
            source_commit="9a9d6e71677104c10a41e22b5a07547a1e5545d0",
            source_path=(
                "data/backtest_sources/kap_bulk_financial_source_capture/"
                "semantic_evidence/insurance_finance_full28_schema_receipt_run_33583866560.json"
            ),
            evidence_domain=EvidenceDomain.FINANCIALS,
            expected_sha256=None,
            authority=ReuseAuthority.DISCOVERY_ONLY,
            coverage_note=(
                "28 real KAP archives, 994 matched reports, 71 source entities and "
                "917 role/row/label identities. Useful for schema/mapping discovery; "
                "source PR explicitly forbids authoritative PIT materialization because "
                "superseded-version enumeration remains unresolved."
            ),
            source_pr=38,
        ),
        CrossRepoArtifactRef(
            source_repository=repo,
            source_commit="9a9d6e71677104c10a41e22b5a07547a1e5545d0",
            source_path=(
                "data/backtest_sources/kap_bulk_financial_source_capture/"
                "public_byte_evidence/acquisition_receipt.run_33568804543.json"
            ),
            evidence_domain=EvidenceDomain.FINANCIALS,
            expected_sha256=None,
            authority=ReuseAuthority.RAW_EVIDENCE_ONLY,
            coverage_note=(
                "Receipt for 28 real KAP financial archives with official download URLs, "
                "observed byte sizes, member counts and SHA256 values. Raw archives may "
                "bootstrap Zincir Kiran once copied/verified, but completeness of historical "
                "superseded versions must be assessed separately."
            ),
            source_pr=38,
        ),
        CrossRepoArtifactRef(
            source_repository=repo,
            source_commit="d0c5ce25832dc94c138fc6141bba8fa8392cd00b",
            source_path="data/audit/w6_ca_gate_reachability_v1/receipt.json",
            evidence_domain=EvidenceDomain.CORPORATE_ACTIONS,
            expected_sha256="1935232295360b1026a036e725809e0e73a62253ce07145bbc1f13fd6abd1345",
            authority=ReuseAuthority.POSITIVE_EVENT_ONLY,
            coverage_note=(
                "KAP corporate-action inventory audit: 60/60 cutoffs reachable, "
                "11680 action events, 699 distinct action tickers. Positive event evidence "
                "is reusable; later-collected inventory alone is not authoritative proof "
                "that no event existed in an interval."
            ),
            source_pr=41,
        ),
        CrossRepoArtifactRef(
            source_repository=repo,
            source_commit="d0c5ce25832dc94c138fc6141bba8fa8392cd00b",
            source_path="data/audit/w7c_real_m2_score_v1/receipt.json",
            evidence_domain=EvidenceDomain.FINANCIALS,
            expected_sha256=None,
            authority=ReuseAuthority.DISCOVERY_ONLY,
            coverage_note=(
                "Seven-ticker, one-cutoff real M2 evidence with production math unchanged. "
                "Useful for validation examples and share-basis methodology; not a full "
                "financial dataset and not a target/label source."
            ),
            source_pr=41,
        ),
    )
    return CrossProjectBootstrapManifest(
        manifest_id="total-rasyo-bootstrap-v1",
        source_project="TOTAL-RASYO-HESAPLAYICI",
        artifacts=tuple(
            sorted(
                artifacts,
                key=lambda item: (
                    item.evidence_domain.value,
                    item.source_commit,
                    item.source_path,
                ),
            )
        ),
        prohibited_source_products=tuple(
            sorted(
                (
                    "DERIVED_TOTAL_RASYO_SCORE_AS_TARGET",
                    "M2_SCORE_AS_FORWARD_RETURN_LABEL",
                    "CURRENT_ONLY_LATEST_FINANCIAL_VIEW_AS_HISTORICAL_PIT",
                    "UNMERGED_EXPERIMENTAL_RESULT_UPGRADED_TO_CANONICAL",
                )
            )
        ),
    )


def reusable_for_canonical_pit(
    artifact: CrossRepoArtifactRef,
) -> bool:
    return artifact.authority is ReuseAuthority.CANONICAL_PIT


def require_canonical_pit(
    artifact: CrossRepoArtifactRef,
) -> None:
    if not reusable_for_canonical_pit(artifact):
        raise ValueError(
            f"artifact is not authorized for canonical PIT: {artifact.authority.value}"
        )
