\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values (
    'context_outside_factor', 'v1', 'QUALITY', 'context_outside_factor',
    'outside', '["x"]'::jsonb
);

insert into zk.factor_experiments (
    experiment_id, factor_id, factor_definition_version, horizon_days,
    data_snapshot_id, universe_rule_version, quantile_count, cost_model_id,
    hypothesis, expected_direction, preregistered_at
) values (
    'context-outside-exp', 'context_outside_factor', 'v1', 20,
    'snap', 'uni', 5, 'cost', 'outside', 'UNDECIDED', now()
);

insert into zk.decorrelation_runs (
    run_id, data_snapshot_id, universe_rule_version, correlation_method,
    minimum_overlap, absolute_threshold, residualization_include_intercept,
    preregistered_at
) values (
    'context-outside-decor', 'snap', 'uni', 'PEARSON',
    20, 0.8, true, now()
);

insert into zk.decorrelation_components (
    run_id, component_no, factor_id, definition_version
) values (
    'context-outside-decor', 1, 'context_outside_factor', 'v1'
);

insert into zk.alpha_factor_admissions (
    admission_id, factor_id, factor_definition_version, horizon_days, decision,
    factor_lab_experiment_id, decorrelation_run_id, decorrelation_component_no,
    rationale
) values (
    'context-outside-adm', 'context_outside_factor', 'v1', 20, 'ADMITTED',
    'context-outside-exp', 'context-outside-decor', 1, 'outside base plan'
);

insert into zk.context_interaction_rules (
    specification_id, definition_version, rule_id,
    left_admission_id, right_admission_id
) values (
    'context-smoke', 'v1', 'outside-rule',
    'alpha-smoke-adm-value', 'context-outside-adm'
);
