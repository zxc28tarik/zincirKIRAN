\set ON_ERROR_STOP on

insert into zk.ml_challenger_specs (
    challenger_id, definition_version, horizon_days,
    universe_rule_version, evaluation_target,
    ridge_penalty, random_seed, preregistered_at
) values (
    'ridge-h20-v1', 'v1', 20,
    'universe-v1', 'future_market_relative_total_return',
    1.0, 17, timestamptz '2026-01-01 00:00:00+00'
);

insert into zk.ml_challenger_features (
    challenger_id, definition_version, feature_id, ordinal
) values
    ('ridge-h20-v1', 'v1', 'momentum', 0),
    ('ridge-h20-v1', 'v1', 'value', 1);

insert into zk.ml_challenger_fits (
    fit_id, challenger_id, definition_version,
    data_snapshot_id, fit_at, training_cutoff,
    training_observations, model_artifact_hash
) values (
    'fit-smoke', 'ridge-h20-v1', 'v1',
    'snapshot-v1', timestamptz '2026-06-01 00:00:00+00',
    timestamptz '2026-05-31 23:59:59+00',
    2, 'sha256:smoke'
);

insert into zk.ml_training_observations (
    fit_id, security_id, observation_at,
    target_available_at, target_value
) values
    ('fit-smoke', 'AAA', timestamptz '2026-01-10 00:00:00+00',
     timestamptz '2026-02-10 00:00:00+00', 0.03),
    ('fit-smoke', 'BBB', timestamptz '2026-02-10 00:00:00+00',
     timestamptz '2026-03-10 00:00:00+00', 0.02);

insert into zk.ml_feature_observations (
    fit_id, security_id, observation_at,
    feature_id, feature_value, available_at
) values
    ('fit-smoke', 'AAA', timestamptz '2026-01-10 00:00:00+00',
     'momentum', 1.0, timestamptz '2026-01-10 00:00:00+00'),
    ('fit-smoke', 'AAA', timestamptz '2026-01-10 00:00:00+00',
     'value', 2.0, timestamptz '2026-01-10 00:00:00+00');

insert into zk.ml_predictions (
    fit_id, security_id, prediction_at, raw_score
) values (
    'fit-smoke', 'AAA', timestamptz '2026-06-02 00:00:00+00', 0.123
);

select fit_id, security_id, prediction_at, raw_score
from zk.ml_predictions
where fit_id = 'fit-smoke';
