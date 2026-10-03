\set ON_ERROR_STOP on

insert into zk.companies (company_id, legal_name)
values ('70000000-0000-0000-0000-000000000001'::uuid, 'Alpha Smoke Company');

insert into zk.securities (security_id, company_id)
values (
    '70000000-0000-0000-0000-000000000002'::uuid,
    '70000000-0000-0000-0000-000000000001'::uuid
);

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values
    ('alpha_smoke_value', 'v1', 'VALUE', 'alpha_smoke_value', 'value', '["x"]'::jsonb),
    ('alpha_smoke_momentum', 'v1', 'PRICE_MOMENTUM', 'alpha_smoke_momentum', 'momentum', '["x"]'::jsonb);

insert into zk.factor_experiments (
    experiment_id, factor_id, factor_definition_version, horizon_days,
    data_snapshot_id, universe_rule_version, quantile_count, cost_model_id,
    hypothesis, expected_direction, preregistered_at
) values
    ('alpha-smoke-exp-value', 'alpha_smoke_value', 'v1', 20, 'snap', 'uni', 5, 'cost', 'value', 'UNDECIDED', now()),
    ('alpha-smoke-exp-mom', 'alpha_smoke_momentum', 'v1', 20, 'snap', 'uni', 5, 'cost', 'mom', 'UNDECIDED', now());

insert into zk.decorrelation_runs (
    run_id, data_snapshot_id, universe_rule_version, correlation_method,
    minimum_overlap, absolute_threshold, residualization_include_intercept, preregistered_at
) values ('alpha-smoke-decor', 'snap', 'uni', 'SPEARMAN', 20, 0.80, true, now());

insert into zk.decorrelation_components (run_id, component_no, factor_id, definition_version)
values
    ('alpha-smoke-decor', 1, 'alpha_smoke_value', 'v1'),
    ('alpha-smoke-decor', 2, 'alpha_smoke_momentum', 'v1');

insert into zk.alpha_aggregation_specs (
    specification_id, definition_version, horizon_days, aggregation_rule_id,
    normalization_rule_id, weight_policy_id, coverage_rule_id, parameters
) values (
    'alpha-engine-smoke', 'v1', 20, 'WEIGHTED_ABS_MEAN',
    'SMOKE_NORM', 'SMOKE_EXPLICIT_WEIGHTS', 'ABS_WEIGHT_COVERAGE',
    '{"minimum_coverage":"0.75"}'::jsonb
);

insert into zk.alpha_factor_admissions (
    admission_id, factor_id, factor_definition_version, horizon_days, decision,
    factor_lab_experiment_id, decorrelation_run_id, decorrelation_component_no, rationale
) values
    ('alpha-smoke-adm-value', 'alpha_smoke_value', 'v1', 20, 'ADMITTED',
     'alpha-smoke-exp-value', 'alpha-smoke-decor', 1, 'smoke'),
    ('alpha-smoke-adm-mom', 'alpha_smoke_momentum', 'v1', 20, 'ADMITTED',
     'alpha-smoke-exp-mom', 'alpha-smoke-decor', 2, 'smoke');

insert into zk.alpha_factor_weights (specification_id, definition_version, admission_id, weight)
values
    ('alpha-engine-smoke', 'v1', 'alpha-smoke-adm-value', 2.0),
    ('alpha-engine-smoke', 'v1', 'alpha-smoke-adm-mom', 1.0);

begin;
insert into zk.alpha_runs (
    alpha_run_id, specification_id, definition_version, security_id, evaluated_at,
    alpha_field, status, alpha_value, coverage, planned_factor_count, available_factor_count,
    planned_absolute_weight, available_absolute_weight
) values (
    'alpha-smoke-run-scored', 'alpha-engine-smoke', 'v1',
    '70000000-0000-0000-0000-000000000002'::uuid, now(),
    'Alpha20', 'SCORED', 0.0, 1.0, 2, 2, 3.0, 3.0
);

insert into zk.alpha_run_contributions (
    alpha_run_id, admission_id, raw_signal_value, normalization_rule_id,
    normalized_value, weight, weighted_contribution
) values
    ('alpha-smoke-run-scored', 'alpha-smoke-adm-value', 0.20, 'SMOKE_NORM', -0.25, 2.0, -0.50),
    ('alpha-smoke-run-scored', 'alpha-smoke-adm-mom', 0.80, 'SMOKE_NORM', 0.50, 1.0, 0.50);
commit;

begin;
insert into zk.alpha_runs (
    alpha_run_id, specification_id, definition_version, security_id, evaluated_at,
    alpha_field, status, alpha_value, coverage, planned_factor_count, available_factor_count,
    planned_absolute_weight, available_absolute_weight
) values (
    'alpha-smoke-run-abstain', 'alpha-engine-smoke', 'v1',
    '70000000-0000-0000-0000-000000000002'::uuid, now(),
    'Alpha20', 'ABSTAIN_INSUFFICIENT_COVERAGE', null, 0.33333333333333333333, 2, 1, 3.0, 1.0
);

insert into zk.alpha_run_contributions (
    alpha_run_id, admission_id, raw_signal_value, normalization_rule_id,
    normalized_value, weight, weighted_contribution
) values (
    'alpha-smoke-run-abstain', 'alpha-smoke-adm-mom', 0.80, 'SMOKE_NORM', 0.50, 1.0, 0.50
);

insert into zk.alpha_run_unavailable_inputs (
    alpha_run_id, admission_id, availability_state, absolute_weight
) values (
    'alpha-smoke-run-abstain', 'alpha-smoke-adm-value', 'MISSING', 2.0
);
commit;

select alpha_run_id, status, alpha_value, coverage
from zk.alpha_runs
where specification_id = 'alpha-engine-smoke'
order by alpha_run_id;
