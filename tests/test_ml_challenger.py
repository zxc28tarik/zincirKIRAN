from datetime import UTC, datetime

import pytest

from zincir_kiran.baselines import Horizon
from zincir_kiran.ml_challenger import (
    MLChallengerSpec,
    MLObservation,
    as_tournament_contender,
    fit_ridge_challenger,
    predict_challenger,
)

PREREGISTERED = datetime(2026, 1, 1, tzinfo=UTC)
FIT_AT = datetime(2026, 6, 1, tzinfo=UTC)


def spec() -> MLChallengerSpec:
    return MLChallengerSpec(
        challenger_id="ridge-h20-v1",
        definition_version="v1",
        horizon=Horizon.H20,
        universe_rule_version="universe-v1",
        evaluation_target="future_market_relative_total_return",
        feature_ids=("momentum", "value"),
        ridge_penalty=1.0,
        preregistered_at=PREREGISTERED,
        random_seed=17,
    )


def row(
    security_id: str,
    when: datetime,
    momentum: float,
    value: float,
    target: float | None = None,
    target_available_at: datetime | None = None,
) -> MLObservation:
    return MLObservation(
        security_id=security_id,
        observation_at=when,
        feature_values=(("momentum", momentum), ("value", value)),
        feature_available_at=(("momentum", when), ("value", when)),
        target_value=target,
        target_available_at=target_available_at,
    )


def training_rows() -> list[MLObservation]:
    return [
        row(
            "AAA",
            datetime(2026, 1, 10, tzinfo=UTC),
            1.0,
            2.0,
            0.03,
            datetime(2026, 2, 10, tzinfo=UTC),
        ),
        row(
            "BBB",
            datetime(2026, 2, 10, tzinfo=UTC),
            2.0,
            1.0,
            0.02,
            datetime(2026, 3, 10, tzinfo=UTC),
        ),
        row(
            "CCC",
            datetime(2026, 3, 10, tzinfo=UTC),
            3.0,
            3.0,
            0.06,
            datetime(2026, 4, 10, tzinfo=UTC),
        ),
    ]


def test_future_feature_evidence_is_rejected() -> None:
    when = datetime(2026, 3, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="future feature evidence"):
        MLObservation(
            security_id="AAA",
            observation_at=when,
            feature_values=(("momentum", 1.0), ("value", 2.0)),
            feature_available_at=(
                ("momentum", datetime(2026, 3, 2, tzinfo=UTC)),
                ("value", when),
            ),
        )


def test_missing_feature_cannot_be_neutral_filled() -> None:
    with pytest.raises(ValueError, match="feature set"):
        fit_ridge_challenger(
            spec(),
            [
                MLObservation(
                    security_id="AAA",
                    observation_at=datetime(2026, 1, 10, tzinfo=UTC),
                    feature_values=(("momentum", 1.0),),
                    feature_available_at=(
                        ("momentum", datetime(2026, 1, 10, tzinfo=UTC)),
                    ),
                    target_value=0.02,
                    target_available_at=datetime(2026, 2, 10, tzinfo=UTC),
                )
            ],
            fit_at=FIT_AT,
        )


def test_future_target_evidence_is_rejected_from_training() -> None:
    rows = training_rows()
    rows[0] = row(
        "AAA",
        datetime(2026, 1, 10, tzinfo=UTC),
        1.0,
        2.0,
        0.03,
        datetime(2026, 7, 1, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="future target evidence"):
        fit_ridge_challenger(spec(), rows, fit_at=FIT_AT)


def test_training_observation_must_precede_fit_cutoff() -> None:
    rows = training_rows() + [
        row(
            "DDD",
            FIT_AT,
            1.0,
            1.0,
            0.01,
            FIT_AT,
        )
    ]
    with pytest.raises(ValueError, match="precede fit_at"):
        fit_ridge_challenger(spec(), rows, fit_at=FIT_AT)


def test_fixed_inputs_produce_deterministic_model_and_predictions() -> None:
    first = fit_ridge_challenger(spec(), training_rows(), fit_at=FIT_AT)
    second = fit_ridge_challenger(spec(), list(reversed(training_rows())), fit_at=FIT_AT)

    assert first == second

    prediction_at = datetime(2026, 6, 2, tzinfo=UTC)
    scoring = [
        row("BBB", prediction_at, 2.5, 2.0),
        row("AAA", prediction_at, 1.5, 2.5),
    ]
    first_predictions = predict_challenger(
        spec(), first, scoring, prediction_at=prediction_at
    )
    second_predictions = predict_challenger(
        spec(), second, list(reversed(scoring)), prediction_at=prediction_at
    )
    assert first_predictions == second_predictions
    assert tuple(item.security_id for item in first_predictions) == ("AAA", "BBB")


def test_prediction_must_follow_model_fit() -> None:
    model = fit_ridge_challenger(spec(), training_rows(), fit_at=FIT_AT)
    with pytest.raises(ValueError, match="strictly follow"):
        predict_challenger(spec(), model, [], prediction_at=FIT_AT)


def test_spec_is_candidate_only_and_feature_order_is_locked() -> None:
    with pytest.raises(ValueError, match="feature_ids must be sorted"):
        MLChallengerSpec(
            challenger_id="bad",
            definition_version="v1",
            horizon=Horizon.H20,
            universe_rule_version="universe-v1",
            evaluation_target="future_market_relative_total_return",
            feature_ids=("value", "momentum"),
            ridge_penalty=1.0,
            preregistered_at=PREREGISTERED,
            random_seed=1,
        )


def test_ml_challenger_registers_only_as_tournament_challenger() -> None:
    contender = as_tournament_contender(
        spec(),
        rationale="Independent nonlinear/linear challenger evidence.",
    )
    assert contender.contender_id == "ridge-h20-v1"
    assert contender.role.value == "CHALLENGER"
    assert contender.artifact_kind == "ML_CHALLENGER"
