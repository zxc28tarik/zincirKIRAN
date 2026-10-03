\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values
    ('decor_bad_a', 'v1', 'QUALITY', 'decor_bad_a', 'a', '["x"]'::jsonb),
    ('decor_bad_b', 'v1', 'QUALITY', 'decor_bad_b', 'b', '["x"]'::jsonb);

insert into zk.decorrelation_runs (
    run_id, data_snapshot_id, universe_rule_version, correlation_method,
    minimum_overlap, absolute_threshold, residualization_include_intercept,
    preregistered_at
) values (
    'decor-bad-pair-v1', 'snapshot-v1', 'universe-v1', 'SPEARMAN',
    20, 0.80, true, now()
);

insert into zk.decorrelation_pair_results (
    run_id,
    left_factor_id, left_definition_version,
    right_factor_id, right_definition_version,
    statistical_state, correlation, overlap_count, concept_edge
) values (
    'decor-bad-pair-v1',
    'decor_bad_a', 'v1',
    'decor_bad_b', 'v1',
    'UNKNOWN', 0.40, 1, false
);
