\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values
    ('decor_resid_a', 'v1', 'RISK', 'decor_resid_a', 'a', '["x"]'::jsonb),
    ('decor_resid_b', 'v1', 'RISK', 'decor_resid_b', 'b', '["x"]'::jsonb);

insert into zk.decorrelation_runs (
    run_id, data_snapshot_id, universe_rule_version, correlation_method,
    minimum_overlap, absolute_threshold, residualization_include_intercept,
    preregistered_at
) values (
    'decor-bad-resid-v1', 'snapshot-v1', 'universe-v1', 'PEARSON',
    20, 0.70, true, now()
);

insert into zk.decorrelation_residualization_results (
    run_id,
    target_factor_id, target_definition_version,
    explanatory_factor_id, explanatory_definition_version,
    residualization_state, overlap_count, intercept, beta
) values (
    'decor-bad-resid-v1',
    'decor_resid_b', 'v1',
    'decor_resid_a', 'v1',
    'INSUFFICIENT_OVERLAP', 2, 0.0, 1.0
);
