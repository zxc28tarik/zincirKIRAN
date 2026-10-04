import pytest

from zincir_kiran.experimental_semantic_bootstrap import (
    PROHIBITED_SOURCE_OUTPUTS,
    SemanticFactAuthority,
    allow_factor_lab_experiment,
    require_authoritative_use,
    total_rasyo_experimental_semantic_corpus,
)


def test_semantic_corpus_counts_match_verified_source() -> None:
    corpus = total_rasyo_experimental_semantic_corpus()
    assert corpus.total_report_count == 5052
    assert corpus.total_fact_count == 199969
    assert corpus.own_period_visible_cells == 5633
    assert corpus.historical_cells == 6000
    assert corpus.authoritative_claim_allowed is False


def test_every_artifact_preserves_experimental_authority_and_risks() -> None:
    corpus = total_rasyo_experimental_semantic_corpus()
    for artifact in corpus.artifacts:
        assert artifact.authority is SemanticFactAuthority.EXPERIMENTAL_VERSION_RISK
        assert "SUPERSEDED_HISTORICAL_KAP_REPORT_VERSIONS_NOT_ENUMERATED" in artifact.risk_ids
        assert "ORIGINAL_CATALOG_BYTES_UNAVAILABLE" in artifact.risk_ids


def test_factor_lab_requires_explicit_experimental_authority() -> None:
    corpus = total_rasyo_experimental_semantic_corpus()
    allow_factor_lab_experiment(
        corpus,
        experiment_authority="EXPERIMENTAL_VERSION_RISK",
    )
    with pytest.raises(ValueError, match="EXPERIMENTAL_VERSION_RISK"):
        allow_factor_lab_experiment(corpus, experiment_authority="AUTHORITATIVE_PIT")


def test_experimental_corpus_cannot_be_promoted_to_authoritative_use() -> None:
    with pytest.raises(ValueError, match="not authorized for authoritative PIT"):
        require_authoritative_use(total_rasyo_experimental_semantic_corpus())


def test_total_rasyo_scores_and_rankings_are_not_imported() -> None:
    assert "TOTAL_RASYO_P4_SCORE" in PROHIBITED_SOURCE_OUTPUTS
    assert "TOTAL_RASYO_RANKING" in PROHIBITED_SOURCE_OUTPUTS
    assert "TOTAL_RASYO_DECISION" in PROHIBITED_SOURCE_OUTPUTS
