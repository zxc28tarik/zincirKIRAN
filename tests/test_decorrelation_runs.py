from datetime import UTC, datetime

import pytest

from zincir_kiran.decorrelation import CorrelationMethod
from zincir_kiran.decorrelation_runs import DecorrelationRunRegistry, DecorrelationRunSpec


def make_spec(**overrides: object) -> DecorrelationRunSpec:
    values: dict[str, object] = {
        "run_id": "decor-v1",
        "data_snapshot_id": "snapshot-1",
        "universe_rule_version": "universe-v1",
        "correlation_method": CorrelationMethod.SPEARMAN,
        "minimum_overlap": 60,
        "absolute_threshold": 0.80,
        "residualization_include_intercept": True,
        "preregistered_at": datetime(2026, 10, 3, tzinfo=UTC),
    }
    values.update(overrides)
    return DecorrelationRunSpec(**values)  # type: ignore[arg-type]


def test_decorrelation_run_captures_all_material_assumptions() -> None:
    spec = make_spec()
    assert spec.correlation_method is CorrelationMethod.SPEARMAN
    assert spec.minimum_overlap == 60
    assert spec.absolute_threshold == 0.80
    assert spec.residualization_include_intercept is True


def test_decorrelation_run_requires_explicit_intercept_choice() -> None:
    with pytest.raises(TypeError):
        DecorrelationRunSpec(
            run_id="decor-v1",
            data_snapshot_id="snapshot-1",
            universe_rule_version="universe-v1",
            correlation_method=CorrelationMethod.PEARSON,
            minimum_overlap=20,
            absolute_threshold=0.75,
            preregistered_at=datetime(2026, 10, 3, tzinfo=UTC),
        )  # type: ignore[call-arg]


def test_decorrelation_run_registry_rejects_conflicting_rewrite() -> None:
    registry = DecorrelationRunRegistry()
    registry.register(make_spec())
    registry.register(make_spec())

    with pytest.raises(ValueError, match="conflicting"):
        registry.register(make_spec(absolute_threshold=0.90))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("run_id", "", "run_id"),
        ("data_snapshot_id", "", "data_snapshot_id"),
        ("universe_rule_version", "", "universe_rule_version"),
        ("minimum_overlap", 1, "minimum_overlap"),
        ("absolute_threshold", 0.0, "absolute_threshold"),
        ("absolute_threshold", 1.01, "absolute_threshold"),
    ],
)
def test_invalid_run_metadata_is_rejected(field: str, value: object, message: str) -> None:
    with pytest.raises((ValueError, TypeError), match=message):
        make_spec(**{field: value})
