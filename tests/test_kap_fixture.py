from pathlib import Path

from zincir_kiran.fixture_validation import validate_kap_fixture


def test_official_kap_fixture_preserves_exact_publication_times() -> None:
    fixture = Path("research/fixtures/kap_thyao_financial_reports_sample.csv")
    assert validate_kap_fixture(fixture) == 4
