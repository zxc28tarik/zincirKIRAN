from datetime import UTC, datetime, timedelta

import pytest

from zincir_kiran.alpha_aggregation import AlphaAggregationSpec
from zincir_kiran.alpha_engine import AlphaFactorWeight
from zincir_kiran.baselines import Horizon
from zincir_kiran.dynamic_evidence import (
    DynamicWeightingRegistry,
    DynamicWeightingSpec,
    DynamicWeightPlanStatus,
    EvidenceMetricObservation,
    EvidenceMetricRule,
    EvidenceTerm,
    FactorEvidenceSnapshot,
    GrossExposurePolicy,
    resolve_dynamic_evidence_weights,
    resolved_alpha_weights,
)
from zincir_kiran.interpretable_alpha import AdmissionDecision, FactorAdmission

PREDICTION = datetime(2026, 10, 4, 9, tzinfo=UTC)


def admission(factor_id: str, component: int) -> FactorAdmission:
    return FactorAdmission(
        admission_id=f"adm-{factor_id}",
        factor_id=factor_id,
        factor_definition_version="v1",
        horizon=Horizon.H20,
        decision=AdmissionDecision.ADMITTED,
        factor_lab_experiment_id=f"exp-{factor_id}",
        decorrelation_run_id="decor-h20",
        decorrelation_component_no=component,
        rationale="test admission",
    )


def base_spec() -> AlphaAggregationSpec:
    return AlphaAggregationSpec(
        specification_id="alpha-h20-base",
        definition_version="v1",
        horizon=Horizon.H20,
        aggregation_rule_id="WEIGHTED_ABS_MEAN",
        normalization_rule_id="ALPHA_NORM",
        weight_policy_id="STATIC_TEST_WEIGHTS",
        coverage_rule_id="ABS_WEIGHT_COVERAGE",
        parameters=(("minimum_coverage", "0.75"),),
    )


def weighting_spec(**overrides: object) -> DynamicWeightingSpec:
    terms = (
        EvidenceTerm(EvidenceMetricRule("icir", "ICIR_FIXED_V1", 0.0, 1.0), 2.0),
        EvidenceTerm(EvidenceMetricRule("long_leg", "LONG_LEG_FIXED_V1", 0.0, 0.10), 1.0),
        EvidenceTerm(EvidenceMetricRule("turnover", "TURNOVER_FIXED_V1", 1.0, 0.0), 1.0),
    )
    values: dict[str, object] = {
        "specification_id": "dynamic-h20",
        "definition_version": "v1",
        "horizon": Horizon.H20,
        "base_alpha_specification_id": "alpha-h20-base",
        "base_alpha_definition_version": "v1",
        "evidence_protocol_id": "rolling-oos-v1",
        "universe_rule_version": "universe-v1",
        "hypothesis": "Recent PIT evidence may improve static admitted-factor weights.",
        "success_criteria": "Beat static-weight comparator OOS after costs without instability.",
        "preregistered_at": PREDICTION - timedelta(days=30),
        "minimum_metric_coverage": 0.75,
        "max_evidence_age_days": 120,
        "multiplier_floor": 0.50,
        "multiplier_ceiling": 1.50,
        "gross_exposure_policy": GrossExposurePolicy.PRESERVE_BASE_ABS_SUM,
        "terms": terms,
    }
    values.update(overrides)
    return DynamicWeightingSpec(**values)  # type: ignore[arg-type]


def snapshot(
    adm: FactorAdmission,
    *,
    snapshot_id: str | None = None,
    metrics: tuple[EvidenceMetricObservation, ...] | None = None,
    window_end: datetime | None = None,
    available_at: datetime | None = None,
) -> FactorEvidenceSnapshot:
    end = window_end or (PREDICTION - timedelta(days=5))
    available = available_at or (end + timedelta(hours=2))
    chosen_metrics = metrics or (
        EvidenceMetricObservation("icir", 0.8),
        EvidenceMetricObservation("long_leg", 0.08),
        EvidenceMetricObservation("turnover", 0.20),
    )
    return FactorEvidenceSnapshot(
        snapshot_id=snapshot_id or f"snap-{adm.factor_id}",
        admission=adm,
        evidence_protocol_id="rolling-oos-v1",
        window_start=end - timedelta(days=90),
        window_end=end,
        available_at=available,
        metrics=chosen_metrics,
    )


def test_metric_rule_handles_higher_and_lower_is_better_without_hidden_direction() -> None:
    higher = EvidenceMetricRule("icir", "v1", 0.0, 1.0)
    lower = EvidenceMetricRule("turnover", "v1", 1.0, 0.0)
    assert higher.normalize(0.5) == pytest.approx(0.5)
    assert lower.normalize(0.25) == pytest.approx(0.75)
    assert higher.normalize(99.0) == 1.0
    assert lower.normalize(99.0) == 0.0


def test_spec_registry_rejects_conflicting_rewrite() -> None:
    registry = DynamicWeightingRegistry()
    item = weighting_spec()
    registry.register(item)
    registry.register(item)
    with pytest.raises(ValueError, match="conflicting"):
        registry.register(weighting_spec(multiplier_ceiling=2.0))


def test_future_evidence_is_rejected_not_ignored() -> None:
    adm = admission("value", 1)
    future = snapshot(
        adm,
        window_end=PREDICTION + timedelta(days=1),
        available_at=PREDICTION + timedelta(days=1, hours=1),
    )
    with pytest.raises(ValueError, match="future evidence"):
        resolve_dynamic_evidence_weights(
            specification=weighting_spec(),
            base_alpha_specification=base_spec(),
            base_weights=[AlphaFactorWeight(adm, 1.0)],
            evidence_snapshots=[future],
            prediction_timestamp=PREDICTION,
        )


def test_stale_evidence_causes_plan_level_abstention() -> None:
    adm = admission("value", 1)
    stale_end = PREDICTION - timedelta(days=121)
    result = resolve_dynamic_evidence_weights(
        specification=weighting_spec(max_evidence_age_days=120),
        base_alpha_specification=base_spec(),
        base_weights=[AlphaFactorWeight(adm, 1.0)],
        evidence_snapshots=[snapshot(adm, window_end=stale_end, available_at=stale_end)],
        prediction_timestamp=PREDICTION,
    )
    assert result.status is DynamicWeightPlanStatus.ABSTAIN_INSUFFICIENT_EVIDENCE
    assert result.insufficient_admission_ids == ("adm-value",)
    assert result.resolved_gross_exposure is None


def test_missing_metric_is_not_neutral_and_below_coverage_abstains() -> None:
    adm = admission("value", 1)
    only_long_leg = (EvidenceMetricObservation("long_leg", 0.08),)
    result = resolve_dynamic_evidence_weights(
        specification=weighting_spec(minimum_metric_coverage=0.75),
        base_alpha_specification=base_spec(),
        base_weights=[AlphaFactorWeight(adm, 1.0)],
        evidence_snapshots=[snapshot(adm, metrics=only_long_leg)],
        prediction_timestamp=PREDICTION,
    )
    assert result.status is DynamicWeightPlanStatus.ABSTAIN_INSUFFICIENT_EVIDENCE


def test_sufficient_partial_evidence_renormalizes_only_after_explicit_coverage_gate() -> None:
    adm = admission("value", 1)
    metrics = (
        EvidenceMetricObservation("icir", 0.50),
        EvidenceMetricObservation("turnover", 0.50),
    )
    result = resolve_dynamic_evidence_weights(
        specification=weighting_spec(minimum_metric_coverage=0.70),
        base_alpha_specification=base_spec(),
        base_weights=[AlphaFactorWeight(adm, 2.0)],
        evidence_snapshots=[snapshot(adm, metrics=metrics)],
        prediction_timestamp=PREDICTION,
    )
    assert result.status is DynamicWeightPlanStatus.RESOLVED
    resolution = result.factor_resolutions[0]
    assert resolution.evidence_coverage == pytest.approx(0.75)
    assert resolution.missing_metric_ids == ("long_leg",)
    assert resolution.evidence_score == pytest.approx(0.5)
    assert resolution.multiplier == pytest.approx(1.0)


def test_dynamic_multiplier_preserves_sign_and_gross_exposure_when_requested() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    result = resolve_dynamic_evidence_weights(
        specification=weighting_spec(),
        base_alpha_specification=base_spec(),
        base_weights=[AlphaFactorWeight(value, 2.0), AlphaFactorWeight(momentum, -1.0)],
        evidence_snapshots=[
            snapshot(value),
            snapshot(
                momentum,
                metrics=(
                    EvidenceMetricObservation("icir", 0.20),
                    EvidenceMetricObservation("long_leg", 0.02),
                    EvidenceMetricObservation("turnover", 0.80),
                ),
            ),
        ],
        prediction_timestamp=PREDICTION,
    )
    assert result.status is DynamicWeightPlanStatus.RESOLVED
    assert result.base_gross_exposure == pytest.approx(3.0)
    assert result.resolved_gross_exposure == pytest.approx(3.0)
    by_factor = {item.factor_id: item for item in result.factor_resolutions}
    assert by_factor["value"].final_weight is not None
    assert by_factor["momentum"].final_weight is not None
    assert by_factor["value"].final_weight > 0
    assert by_factor["momentum"].final_weight < 0


def test_plan_abstains_if_one_of_multiple_factors_has_no_snapshot() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    result = resolve_dynamic_evidence_weights(
        specification=weighting_spec(),
        base_alpha_specification=base_spec(),
        base_weights=[AlphaFactorWeight(value, 1.0), AlphaFactorWeight(momentum, 1.0)],
        evidence_snapshots=[snapshot(value)],
        prediction_timestamp=PREDICTION,
    )
    assert result.status is DynamicWeightPlanStatus.ABSTAIN_INSUFFICIENT_EVIDENCE
    assert result.insufficient_admission_ids == ("adm-momentum",)
    assert all(item.final_weight is None for item in result.factor_resolutions)


def test_resolved_weights_preserve_one_vote_per_component() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    result = resolve_dynamic_evidence_weights(
        specification=weighting_spec(),
        base_alpha_specification=base_spec(),
        base_weights=[AlphaFactorWeight(value, 1.0), AlphaFactorWeight(momentum, 1.0)],
        evidence_snapshots=[snapshot(momentum), snapshot(value)],
        prediction_timestamp=PREDICTION,
    )
    weights = resolved_alpha_weights(result, admissions=(momentum, value))
    assert tuple(item.admission.factor_id for item in weights) == ("momentum", "value")


def test_duplicate_component_is_still_blocked_before_dynamic_weighting() -> None:
    first = admission("momentum_12_1", 1)
    second = FactorAdmission(
        admission_id="adm-momentum-6-1",
        factor_id="momentum_6_1",
        factor_definition_version="v1",
        horizon=Horizon.H20,
        decision=AdmissionDecision.ADMITTED,
        factor_lab_experiment_id="exp-momentum-6-1",
        decorrelation_run_id="decor-h20",
        decorrelation_component_no=1,
        rationale="same component",
    )
    with pytest.raises(ValueError, match="duplicate de-correlation vote"):
        resolve_dynamic_evidence_weights(
            specification=weighting_spec(),
            base_alpha_specification=base_spec(),
            base_weights=[AlphaFactorWeight(first, 1.0), AlphaFactorWeight(second, 1.0)],
            evidence_snapshots=[snapshot(first), snapshot(second)],
            prediction_timestamp=PREDICTION,
        )


def test_fixed_inputs_are_deterministic_independent_of_input_order() -> None:
    value = admission("value", 1)
    momentum = admission("momentum", 2)
    kwargs = {
        "specification": weighting_spec(),
        "base_alpha_specification": base_spec(),
        "prediction_timestamp": PREDICTION,
    }
    first = resolve_dynamic_evidence_weights(
        **kwargs,
        base_weights=[AlphaFactorWeight(value, 2.0), AlphaFactorWeight(momentum, 1.0)],
        evidence_snapshots=[snapshot(value), snapshot(momentum)],
    )
    second = resolve_dynamic_evidence_weights(
        **kwargs,
        base_weights=[AlphaFactorWeight(momentum, 1.0), AlphaFactorWeight(value, 2.0)],
        evidence_snapshots=[snapshot(momentum), snapshot(value)],
    )
    assert first == second

def test_weighting_protocol_must_be_preregistered_before_prediction() -> None:
    adm = admission("value", 1)
    with pytest.raises(ValueError, match="preregistered"):
        resolve_dynamic_evidence_weights(
            specification=weighting_spec(
                preregistered_at=PREDICTION + timedelta(seconds=1)
            ),
            base_alpha_specification=base_spec(),
            base_weights=[AlphaFactorWeight(adm, 1.0)],
            evidence_snapshots=[snapshot(adm)],
            prediction_timestamp=PREDICTION,
        )


def test_snapshot_protocol_must_match_preregistered_protocol() -> None:
    adm = admission("value", 1)
    wrong = FactorEvidenceSnapshot(
        snapshot_id="wrong-protocol",
        admission=adm,
        evidence_protocol_id="post-hoc-protocol",
        window_start=PREDICTION - timedelta(days=90),
        window_end=PREDICTION - timedelta(days=5),
        available_at=PREDICTION - timedelta(days=4),
        metrics=(
            EvidenceMetricObservation("icir", 0.8),
            EvidenceMetricObservation("long_leg", 0.08),
            EvidenceMetricObservation("turnover", 0.2),
        ),
    )
    with pytest.raises(ValueError, match="protocol"):
        resolve_dynamic_evidence_weights(
            specification=weighting_spec(),
            base_alpha_specification=base_spec(),
            base_weights=[AlphaFactorWeight(adm, 1.0)],
            evidence_snapshots=[wrong],
            prediction_timestamp=PREDICTION,
        )
