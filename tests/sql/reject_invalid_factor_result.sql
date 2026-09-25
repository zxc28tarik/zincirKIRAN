\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values (
    'lab_bad_result_factor', 'v1', 'RISK', 'lab_bad_result',
    'test', '["x"]'::jsonb
);

insert into zk.factor_experiments (
    experiment_id, factor_id, factor_definition_version, horizon_days,
    data_snapshot_id, universe_rule_version, quantile_count, cost_model_id,
    hypothesis, expected_direction, preregistered_at
) values (
    'bad-result-exp', 'lab_bad_result_factor', 'v1', 120,
    'snapshot-v1', 'universe-v1', 5, 'cost-v1',
    'test', 'LOWER_IS_BETTER', now()
);

insert into zk.factor_lab_results (
    experiment_id, total_periods, valid_ic_periods, mean_coverage, q_value
) values (
    'bad-result-exp', 10, 11, 1.2, 1.5
);
