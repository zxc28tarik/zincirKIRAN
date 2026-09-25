\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values (
    'lab_immutable_factor', 'v1', 'QUALITY', 'lab_immutable',
    'test', '["x"]'::jsonb
);

insert into zk.factor_experiments (
    experiment_id, factor_id, factor_definition_version, horizon_days,
    data_snapshot_id, universe_rule_version, quantile_count, cost_model_id,
    hypothesis, expected_direction, preregistered_at
) values (
    'immutable-exp', 'lab_immutable_factor', 'v1', 60,
    'snapshot-v1', 'universe-v1', 5, 'cost-v1',
    'pre-registered hypothesis', 'UNDECIDED', now()
);

update zk.factor_experiments
set quantile_count = 10
where experiment_id = 'immutable-exp';
