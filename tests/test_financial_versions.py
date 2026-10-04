from datetime import UTC, datetime

import pytest

from zincir_kiran.financial_versions import (
    KORTS_P7_SOURCE_RECEIPT_SHA256,
    FinancialVersion,
    FinancialVersionChain,
    VersionAuthority,
    korts_2022_revision_fixture,
    require_authoritative_factor_input,
    select_version_at_cutoff,
)


def test_korts_real_revision_chain_selects_original_before_correction() -> None:
    chain = korts_2022_revision_fixture()
    cutoff = datetime(2023, 3, 15, 12, 0, tzinfo=UTC)
    selected = select_version_at_cutoff(chain, cutoff_at=cutoff)
    assert selected is not None
    assert selected.disclosure_id == "1122417"


def test_korts_real_revision_chain_selects_correction_after_publication() -> None:
    chain = korts_2022_revision_fixture()
    cutoff = datetime(2023, 3, 22, 12, 0, tzinfo=UTC)
    selected = select_version_at_cutoff(chain, cutoff_at=cutoff)
    assert selected is not None
    assert selected.disclosure_id == "1126845"


def test_no_statement_visible_before_original_publication() -> None:
    chain = korts_2022_revision_fixture()
    cutoff = datetime(2023, 3, 1, 12, 0, tzinfo=UTC)
    assert select_version_at_cutoff(chain, cutoff_at=cutoff) is None


def test_authoritative_chain_requires_complete_enumeration() -> None:
    version = FinancialVersion(
        ticker="AAA",
        period_end="2024-12-31",
        disclosure_id="1",
        published_at=datetime(2025, 3, 1, tzinfo=UTC),
        raw_sha256="a" * 64,
        version_sequence=1,
        version_tag="ORIGINAL",
    )
    with pytest.raises(ValueError, match="complete version enumeration"):
        FinancialVersionChain(
            ticker="AAA",
            period_end="2024-12-31",
            versions=(version,),
            enumeration_complete=False,
            authority=VersionAuthority.AUTHORITATIVE_PIT,
        )


def test_bulk_latest_only_cannot_feed_authoritative_factor() -> None:
    version = FinancialVersion(
        ticker="AAA",
        period_end="2024-12-31",
        disclosure_id="2",
        published_at=datetime(2025, 3, 15, tzinfo=UTC),
        raw_sha256="b" * 64,
        version_sequence=2,
        version_tag="LATEST_OBSERVED",
    )
    chain = FinancialVersionChain(
        ticker="AAA",
        period_end="2024-12-31",
        versions=(version,),
        enumeration_complete=False,
        authority=VersionAuthority.BULK_LATEST_ONLY,
    )
    with pytest.raises(ValueError, match="not authorized"):
        require_authoritative_factor_input(chain)


def test_cutoff_selection_refuses_experimental_version_risk() -> None:
    version = FinancialVersion(
        ticker="AAA",
        period_end="2024-12-31",
        disclosure_id="1",
        published_at=datetime(2025, 3, 1, tzinfo=UTC),
        raw_sha256="c" * 64,
        version_sequence=1,
        version_tag="OBSERVED",
    )
    chain = FinancialVersionChain(
        ticker="AAA",
        period_end="2024-12-31",
        versions=(version,),
        enumeration_complete=False,
        authority=VersionAuthority.EXPERIMENTAL_VERSION_RISK,
    )
    with pytest.raises(ValueError, match="requires AUTHORITATIVE_PIT"):
        select_version_at_cutoff(chain, cutoff_at=datetime(2025, 3, 2, tzinfo=UTC))


def test_source_receipt_is_hash_pinned() -> None:
    assert len(KORTS_P7_SOURCE_RECEIPT_SHA256) == 64
