\set ON_ERROR_STOP on
begin;
insert into zk.alpha_runs (
    alpha_run_id, specification_id, definition_version, security_id, evaluated_at,
    alpha_field, status, alpha_value, coverage, planned_factor_count, available_factor_count,
    planned_absolute_weight, available_absolute_weight
) values (
    'alpha-bad-eligibility-run', 'alpha-engine-smoke', 'v1',
    '70000000-0000-0000-0000-000000000002'::uuid, now(),
    'Alpha20', 'SCORED', 0.0, 1.0, 2, 2, 3.0, 3.0
);
insert into zk.alpha_run_contributions (
    alpha_run_id, admission_id, raw_signal_value, normalization_rule_id,
    applicability_state, accounting_comparability_state,
    normalized_value, weight, weighted_contribution
) values (
    'alpha-bad-eligibility-run', 'alpha-smoke-adm-mom', 0.80, 'SMOKE_NORM',
    'UNDECIDED', 'COMPARABLE', 0.50, 1.0, 0.50
);
commit;
