\set ON_ERROR_STOP on
begin;
insert into zk.dynamic_weight_runs (
    dynamic_run_id, specification_id, definition_version, prediction_timestamp,
    status, base_gross_exposure, preliminary_gross_exposure,
    resolved_gross_exposure, gross_rescale_factor
) values (
    'dynamic-bad-arithmetic-run', 'dynamic-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'RESOLVED', 3.0, 3.5, 3.0, (6::numeric / 7)
);

insert into zk.dynamic_weight_factor_results (
    dynamic_run_id, admission_id, snapshot_id, base_weight,
    evidence_coverage, evidence_score, multiplier,
    preliminary_weight, final_weight
) values
    (
        'dynamic-bad-arithmetic-run', 'alpha-smoke-adm-value', 'dynamic-snap-value',
        2.0, 1.0, 0.60, 1.10, 2.2, (15::numeric / 7)
    ),
    (
        'dynamic-bad-arithmetic-run', 'alpha-smoke-adm-mom', 'dynamic-snap-mom',
        1.0, 1.0, 0.50, 1.00, 1.0, (6::numeric / 7)
    );

insert into zk.dynamic_weight_metric_contributions (
    dynamic_run_id, admission_id, metric_id, normalization_rule_id,
    raw_value, normalized_quality, coefficient, weighted_quality_contribution
) values
    ('dynamic-bad-arithmetic-run', 'alpha-smoke-adm-value', 'icir', 'ICIR_FIXED_V1', 0.75, 0.75, 2.0, 1.50),
    ('dynamic-bad-arithmetic-run', 'alpha-smoke-adm-value', 'long_leg', 'LONG_LEG_FIXED_V1', 0.075, 0.75, 1.0, 0.75),
    ('dynamic-bad-arithmetic-run', 'alpha-smoke-adm-value', 'turnover', 'TURNOVER_FIXED_V1', 0.25, 0.75, 1.0, 0.75),
    ('dynamic-bad-arithmetic-run', 'alpha-smoke-adm-mom', 'icir', 'ICIR_FIXED_V1', 0.50, 0.50, 2.0, 1.00),
    ('dynamic-bad-arithmetic-run', 'alpha-smoke-adm-mom', 'long_leg', 'LONG_LEG_FIXED_V1', 0.05, 0.50, 1.0, 0.50),
    ('dynamic-bad-arithmetic-run', 'alpha-smoke-adm-mom', 'turnover', 'TURNOVER_FIXED_V1', 0.50, 0.50, 1.0, 0.50);
commit;
