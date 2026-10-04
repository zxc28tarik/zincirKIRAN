import pytest

from zincir_kiran.price_factor_diagnostic import (
    FACTORS,
    PriceFactorDiagnosticSpec,
)


def test_locked_price_factor_diagnostic_scope() -> None:
    spec = PriceFactorDiagnosticSpec()
    assert spec.factors == tuple(sorted(FACTORS))
    assert spec.horizons == (20, 60, 120, 252)
    assert spec.target_authority == "DIAGNOSTIC_RETURN_PROXY"
    assert spec.production_ready is False


def test_diagnostic_cannot_be_marked_production_ready() -> None:
    with pytest.raises(ValueError, match="cannot be production-ready"):
        PriceFactorDiagnosticSpec(production_ready=True)
