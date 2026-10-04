\set ON_ERROR_STOP on
insert into zk.ml_challenger_specs (
    challenger_id, definition_version, horizon_days,
    universe_rule_version, evaluation_target,
    ridge_penalty, random_seed, preregistered_at
) values (
    'reject-ml-mutation', 'v1', 20, 'universe-v1',
    'future_market_relative_total_return', 1.0, 1,
    timestamptz '2026-01-01 00:00:00+00'
);
update zk.ml_challenger_specs
set ridge_penalty = 2.0
where challenger_id = 'reject-ml-mutation' and definition_version = 'v1';
