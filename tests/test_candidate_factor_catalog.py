import csv
from pathlib import Path

from zincir_kiran.factor_library import EconomicFamily, EvidenceStatus, FactorStage


def test_candidate_catalog_covers_all_families_and_is_not_promoted() -> None:
    path = Path("research/candidate_factors_v0.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) >= 40
    assert {row["economic_family"] for row in rows} == {family.value for family in EconomicFamily}
    assert {row["stage"] for row in rows} == {FactorStage.CANDIDATE.value}
    assert {row["evidence_status"] for row in rows} == {EvidenceStatus.UNREVIEWED.value}
    assert len({row["factor_id"] for row in rows}) == len(rows)
    assert all(row["economic_concept_key"].strip() for row in rows)
    assert all(row["required_fields"].strip() for row in rows)


def test_catalog_keeps_related_definitions_under_shared_concepts() -> None:
    path = Path("research/candidate_factors_v0.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    momentum = [row for row in rows if row["economic_concept_key"] == "medium_term_momentum"]
    revisions = [row for row in rows if row["economic_concept_key"] == "estimate_revision"]

    assert {row["factor_id"] for row in momentum} == {"momentum_12_1", "momentum_6_1"}
    assert {row["factor_id"] for row in revisions} == {"eps_revision", "revenue_revision"}
