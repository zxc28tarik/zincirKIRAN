from datetime import UTC, datetime

import pytest

from zincir_kiran.official_acquisition import (
    AcquiredArtifactReceipt,
    AcquisitionAttempt,
    AcquisitionStatus,
    official_source_ids,
    validate_acquisition_source,
)

NOW = datetime(2026, 10, 4, 13, 50, tzinfo=UTC)


def test_official_sources_include_kap_and_borsa_istanbul() -> None:
    assert official_source_ids() == {"borsa_istanbul", "kap"}


def test_unknown_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown official/public source"):
        validate_acquisition_source("unknown")


def test_successful_acquisition_cannot_hide_blocker() -> None:
    with pytest.raises(ValueError, match="cannot carry blocker"):
        AcquisitionAttempt(
            acquisition_id="a1",
            source_id="kap",
            requested_url="https://kap.org.tr",
            attempted_at=NOW,
            status=AcquisitionStatus.ACQUIRED,
            blocker_code="NO",
            blocker_detail="should not exist",
        )


def test_blocked_acquisition_requires_explicit_reason() -> None:
    with pytest.raises(ValueError, match="requires blocker_code"):
        AcquisitionAttempt(
            acquisition_id="a1",
            source_id="borsa_istanbul",
            requested_url="https://www.borsaistanbul.com",
            attempted_at=NOW,
            status=AcquisitionStatus.BLOCKED,
        )


def test_artifact_receipt_hashes_exact_bytes() -> None:
    receipt = AcquiredArtifactReceipt.from_bytes(
        acquisition_id="a1",
        source_id="kap",
        source_url="https://kap.org.tr/example",
        retrieved_at=NOW,
        content=b"exact bytes",
        media_type="text/html",
    )
    assert receipt.byte_size == 11
    assert len(receipt.content_sha256) == 64
