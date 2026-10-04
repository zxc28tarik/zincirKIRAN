from datetime import UTC, date, datetime

import pytest

from zincir_kiran.baselines import Horizon
from zincir_kiran.tournament import (
    ContenderRole,
    FoldMetricObservation,
    MetricDirection,
    TournamentContender,
    TournamentDecision,
    TournamentMetricSpec,
    TournamentRegistry,
    TournamentSpec,
    WalkForwardFold,
    aggregate_fold_metrics,
    build_tournament_outcome,
    multiple_testing_evidence,
    paired_champion_differences,
)

PREREGISTERED = datetime(2026, 1, 1, tzinfo=UTC)


def contenders() -> tuple[TournamentContender, ...]:
    return (
        TournamentContender(
            "dynamic",
            ContenderRole.CHALLENGER,
            "DYNAMIC_ALPHA",
            "dynamic-h20",
            "v1",
            "Dynamic evidence weighting challenger.",
        ),
        TournamentContender(
            "static",
            ContenderRole.CHAMPION,
            "INTERPRETABLE_ALPHA",
            "alpha-h20",
            "v1",
            "Static interpretable champion.",
        ),
    )


def folds() -> tuple[WalkForwardFold, ...]:
    return (
        WalkForwardFold(
            "fold-1",
            date(2020, 1, 1),
            date(2021, 12, 31),
            date(2022, 1, 3),
            date(2022, 12, 30),
        ),
        WalkForwardFold(
            "fold-2",
            date(2020, 1, 1),
            date(2022, 12, 30),
            date(2023, 1, 3),
            date(2023, 12, 29),
        ),
        WalkForwardFold(
            "fold-3",
            date(2020, 1, 1),
            date(2023, 12, 29),
            date(2024, 1, 2),
            date(2024, 12, 31),
        ),
    )


def metrics() -> tuple[TournamentMetricSpec, ...]:
    return (
        TournamentMetricSpec("max_drawdown", MetricDirection.LOWER_IS_BETTER, True),
        TournamentMetricSpec(
            "net_return_after_costs",
            MetricDirection.HIGHER_IS_BETTER,
            True,
            requires_cost_model=True,
        ),
        TournamentMetricSpec("sharpe", MetricDirection.HIGHER_IS_BETTER, True),
    )


def spec(**overrides: object) -> TournamentSpec:
    values: dict[str, object] = {
        "tournament_id": "wf-h20-v1",
        "definition_version": "v1",
        "horizon": Horizon.H20,
        "universe_rule_version": "universe-v1",
        "evaluation_target": "future_market_relative_total_return",
        "hypothesis": "Challengers may improve OOS evidence without hidden leakage.",
        "success_criteria": "Review only after robust multi-metric OOS evidence.",
        "preregistered_at": PREREGISTERED,
        "purge_days": 1,
        "embargo_days": 1,
        "multiple_testing_method": "BENJAMINI_HOCHBERG",
        "primary_metric_id": "net_return_after_costs",
        "contenders": contenders(),
        "folds": folds(),
        "metrics": metrics(),
    }
    values.update(overrides)
    return TournamentSpec(**values)  # type: ignore[arg-type]


def observations() -> list[FoldMetricObservation]:
    rows: list[FoldMetricObservation] = []
    static = {
        "fold-1": (0.08, 0.90, -0.20),
        "fold-2": (0.10, 1.00, -0.18),
        "fold-3": (0.06, 0.80, -0.22),
    }
    dynamic = {
        "fold-1": (0.09, 0.95, -0.19),
        "fold-2": (None, 1.10, -0.17),
        "fold-3": (0.07, 0.85, -0.25),
    }
    for contender_id, values_by_fold in (("static", static), ("dynamic", dynamic)):
        for fold_id, (net_return, sharpe, drawdown) in values_by_fold.items():
            rows.extend(
                [
                    FoldMetricObservation(
                        contender_id,
                        fold_id,
                        "net_return_after_costs",
                        net_return,
                        100,
                        cost_model_id="cost-v1" if net_return is not None else None,
                    ),
                    FoldMetricObservation(contender_id, fold_id, "sharpe", sharpe, 100),
                    FoldMetricObservation(
                        contender_id, fold_id, "max_drawdown", drawdown, 100
                    ),
                ]
            )
    return rows


def test_registry_rejects_conflicting_rewrite() -> None:
    registry = TournamentRegistry()
    item = spec()
    registry.register(item)
    registry.register(item)
    with pytest.raises(ValueError, match="conflicting"):
        registry.register(spec(success_criteria="changed after results"))


def test_walk_forward_requires_chronological_train_then_validation() -> None:
    with pytest.raises(ValueError, match="train_end < validation_start"):
        WalkForwardFold(
            "bad",
            date(2020, 1, 1),
            date(2022, 1, 5),
            date(2022, 1, 5),
            date(2022, 12, 31),
        )


def test_purge_and_embargo_are_explicitly_enforced() -> None:
    with pytest.raises(ValueError, match="purge_days"):
        spec(purge_days=3)

    overlapping = (
        folds()[0],
        WalkForwardFold(
            "fold-2",
            date(2020, 1, 1),
            date(2022, 6, 1),
            date(2022, 12, 30),
            date(2023, 6, 30),
        ),
    )
    with pytest.raises(ValueError, match="overlap"):
        spec(folds=overlapping)

    no_embargo_gap = (
        folds()[0],
        WalkForwardFold(
            "fold-2",
            date(2020, 1, 1),
            date(2022, 12, 30),
            date(2022, 12, 31),
            date(2023, 12, 29),
        ),
    )
    with pytest.raises(ValueError, match="embargo_days"):
        spec(folds=no_embargo_gap)


def test_exactly_one_champion_is_required() -> None:
    both_challengers = tuple(
        TournamentContender(
            item.contender_id,
            ContenderRole.CHALLENGER,
            item.artifact_kind,
            item.artifact_specification_id,
            item.artifact_definition_version,
            item.rationale,
        )
        for item in contenders()
    )
    with pytest.raises(ValueError, match="exactly one CHAMPION"):
        spec(contenders=both_challengers)


def test_missing_fold_metric_stays_missing_not_zero() -> None:
    aggregates = aggregate_fold_metrics(spec(), observations())
    item = next(
        value
        for value in aggregates
        if value.contender_id == "dynamic"
        and value.metric_id == "net_return_after_costs"
    )
    assert item.valid_folds == 2
    assert item.total_folds == 3
    assert item.mean_value == pytest.approx(0.08)


def test_cost_aware_metric_requires_explicit_cost_model() -> None:
    bad = [
        FoldMetricObservation(
            "static",
            "fold-1",
            "net_return_after_costs",
            0.10,
            100,
            cost_model_id=None,
        )
    ]
    with pytest.raises(ValueError, match="cost_model_id"):
        aggregate_fold_metrics(spec(), bad)


def test_paired_difference_uses_only_folds_where_both_values_exist() -> None:
    results = paired_champion_differences(spec(), observations())
    net = next(
        item
        for item in results
        if item.challenger_id == "dynamic"
        and item.metric_id == "net_return_after_costs"
    )
    assert net.paired_folds == 2
    assert net.mean_difference_vs_champion == pytest.approx(0.01)

    drawdown = next(
        item
        for item in results
        if item.challenger_id == "dynamic" and item.metric_id == "max_drawdown"
    )
    # LOWER_IS_BETTER: fold deltas are +0.01, +0.01, -0.03 after direction flip.
    assert drawdown.mean_difference_vs_champion == pytest.approx(-1 / 300)


def test_benjamini_hochberg_qvalues_are_attached_to_preregistered_challengers() -> None:
    result = multiple_testing_evidence(
        spec(),
        {
            ("dynamic", "net_return_after_costs"): 0.01,
            ("dynamic", "sharpe"): 0.04,
        },
    )
    by_metric = {item.metric_id: item for item in result}
    assert by_metric["net_return_after_costs"].qvalue == pytest.approx(0.02)
    assert by_metric["sharpe"].qvalue == pytest.approx(0.04)


def test_champion_is_never_auto_promoted_away_by_tournament_builder() -> None:
    outcome = build_tournament_outcome(
        specification=spec(),
        observations=observations(),
        pvalues={
            ("dynamic", "net_return_after_costs"): 0.001,
            ("dynamic", "sharpe"): 0.001,
        },
    )
    assert outcome.champion_id == "static"
    assert outcome.decision is TournamentDecision.RETAIN_CHAMPION_REVIEW_REQUIRED
    assert outcome.automatic_promotion is False
    assert outcome.review_required is True


def test_fold_metric_unknown_entities_are_rejected() -> None:
    with pytest.raises(ValueError, match="not preregistered"):
        aggregate_fold_metrics(
            spec(),
            [FoldMetricObservation("unknown", "fold-1", "sharpe", 1.0, 10)],
        )
    with pytest.raises(ValueError, match="fold is not preregistered"):
        aggregate_fold_metrics(
            spec(),
            [FoldMetricObservation("static", "fold-X", "sharpe", 1.0, 10)],
        )


def test_fixed_inputs_produce_deterministic_outcome() -> None:
    first = build_tournament_outcome(
        specification=spec(),
        observations=observations(),
        pvalues={
            ("dynamic", "net_return_after_costs"): 0.02,
            ("dynamic", "sharpe"): 0.03,
        },
    )
    second = build_tournament_outcome(
        specification=spec(),
        observations=list(reversed(observations())),
        pvalues={
            ("dynamic", "sharpe"): 0.03,
            ("dynamic", "net_return_after_costs"): 0.02,
        },
    )
    assert first == second
