\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values
    ('decor_factor_a', 'v1', 'VALUE', 'decor_a', 'a', '["x"]'::jsonb),
    ('decor_factor_b', 'v1', 'VALUE', 'decor_b', 'b', '["x"]'::jsonb);

insert into zk.decorrelation_runs (
    run_id, data_snapshot_id, universe_rule_version, correlation_method,
    minimum_overlap, absolute_threshold, residualization_include_intercept,
    preregistered_at
) values (
    'decor-smoke-v1', 'snapshot-v1', 'universe-v1', 'SPEARMAN',
    60, 0.80, true, timestamptz '2026-10-03 12:00:00+03'
);

insert into zk.decorrelation_pair_results (
    run_id,
    left_factor_id, left_definition_version,
    right_factor_id, right_definition_version,
    statistical_state, correlation, overlap_count, concept_edge
) values (
    'decor-smoke-v1',
    'decor_factor_a', 'v1',
    'decor_factor_b', 'v1',
    'REDUNDANCY_CANDIDATE', 0.91, 100, false
);

insert into zk.decorrelation_components (
    run_id, component_no, factor_id, definition_version
) values
    ('decor-smoke-v1', 1, 'decor_factor_a', 'v1'),
    ('decor-smoke-v1', 1, 'decor_factor_b', 'v1');

insert into zk.decorrelation_residualization_results (
    run_id,
    target_factor_id, target_definition_version,
    explanatory_factor_id, explanatory_definition_version,
    residualization_state, overlap_count, intercept, beta
) values (
    'decor-smoke-v1',
    'decor_factor_b', 'v1',
    'decor_factor_a', 'v1',
    'ESTIMATED', 100, 0.10, 0.75
);

select run_id, correlation_method, minimum_overlap, absolute_threshold
from zk.decorrelation_runs
where run_id = 'decor-smoke-v1';
