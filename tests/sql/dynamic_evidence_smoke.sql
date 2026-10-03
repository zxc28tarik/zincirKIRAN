\set ON_ERROR_STOP on

insert into zk.dynamic_weighting_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    minimum_metric_coverage, max_evidence_age_days,
    multiplier_floor, multiplier_ceiling, gross_exposure_policy
) values (
    'dynamic-smoke', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    0.75, 120, 0.50, 1.50, 'PRESERVE_BASE_ABS_SUM'
);

insert into zk.dynamic_evidence_terms (
    specification_id, definition_version, metric_id, normalization_rule_id,
    bad_reference, good_reference, coefficient
) values
    ('dynamic-smoke', 'v1', 'icir', 'ICIR_FIXED_V1', 0.0, 1.0, 2.0),
    ('dynamic-smoke', 'v1', 'long_leg', 'LONG_LEG_FIXED_V1', 0.0, 0.10, 1.0),
    ('dynamic-smoke', 'v1', 'turnover', 'TURNOVER_FIXED_V1', 1.0, 0.0, 1.0);

insert into zk.dynamic_evidence_snapshots (
    snapshot_id, admission_id, evidence_protocol_id,
    window_start, window_end, available_at
) values
    (
        'dynamic-snap-value', 'alpha-smoke-adm-value', 'rolling-oos-v1',
        timestamptz '2026-06-01 00:00:00+00',
        timestamptz '2026-09-29 00:00:00+00',
        timestamptz '2026-09-29 02:00:00+00'
    ),
    (
        'dynamic-snap-mom', 'alpha-smoke-adm-mom', 'rolling-oos-v1',
        timestamptz '2026-06-01 00:00:00+00',
        timestamptz '2026-09-29 00:00:00+00',
        timestamptz '2026-09-29 02:00:00+00'
    );

insert into zk.dynamic_evidence_metric_values (snapshot_id, metric_id, raw_value)
values
    ('dynamic-snap-value', 'icir', 0.75),
    ('dynamic-snap-value', 'long_leg', 0.075),
    ('dynamic-snap-value', 'turnover', 0.25),
    ('dynamic-snap-mom', 'icir', 0.50),
    ('dynamic-snap-mom', 'long_leg', 0.05),
    ('dynamic-snap-mom', 'turnover', 0.50);

begin;
insert into zk.dynamic_weight_runs (
    dynamic_run_id, specification_id, definition_version, prediction_timestamp,
    status, base_gross_exposure, preliminary_gross_exposure,
    resolved_gross_exposure, gross_rescale_factor
) values (
    'dynamic-run-resolved', 'dynamic-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'RESOLVED', 3.0, 3.5, 3.0, (6::numeric / 7)
);

insert into zk.dynamic_weight_factor_results (
    dynamic_run_id, admission_id, snapshot_id, base_weight,
    evidence_coverage, evidence_score, multiplier,
    preliminary_weight, final_weight
) values
    (
        'dynamic-run-resolved', 'alpha-smoke-adm-value', 'dynamic-snap-value',
        2.0, 1.0, 0.75, 1.25, 2.5, (15::numeric / 7)
    ),
    (
        'dynamic-run-resolved', 'alpha-smoke-adm-mom', 'dynamic-snap-mom',
        1.0, 1.0, 0.50, 1.00, 1.0, (6::numeric / 7)
    );

insert into zk.dynamic_weight_metric_contributions (
    dynamic_run_id, admission_id, metric_id, normalization_rule_id,
    raw_value, normalized_quality, coefficient, weighted_quality_contribution
) values
    ('dynamic-run-resolved', 'alpha-smoke-adm-value', 'icir', 'ICIR_FIXED_V1', 0.75, 0.75, 2.0, 1.50),
    ('dynamic-run-resolved', 'alpha-smoke-adm-value', 'long_leg', 'LONG_LEG_FIXED_V1', 0.075, 0.75, 1.0, 0.75),
    ('dynamic-run-resolved', 'alpha-smoke-adm-value', 'turnover', 'TURNOVER_FIXED_V1', 0.25, 0.75, 1.0, 0.75),
    ('dynamic-run-resolved', 'alpha-smoke-adm-mom', 'icir', 'ICIR_FIXED_V1', 0.50, 0.50, 2.0, 1.00),
    ('dynamic-run-resolved', 'alpha-smoke-adm-mom', 'long_leg', 'LONG_LEG_FIXED_V1', 0.05, 0.50, 1.0, 0.50),
    ('dynamic-run-resolved', 'alpha-smoke-adm-mom', 'turnover', 'TURNOVER_FIXED_V1', 0.50, 0.50, 1.0, 0.50);
commit;

begin;
insert into zk.dynamic_weight_runs (
    dynamic_run_id, specification_id, definition_version, prediction_timestamp,
    status, base_gross_exposure, preliminary_gross_exposure,
    resolved_gross_exposure, gross_rescale_factor
) values (
    'dynamic-run-abstain', 'dynamic-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_EVIDENCE', 3.0, null, null, null
);

insert into zk.dynamic_weight_factor_results (
    dynamic_run_id, admission_id, snapshot_id, base_weight,
    evidence_coverage, evidence_score, multiplier,
    preliminary_weight, final_weight
) values (
    'dynamic-run-abstain', 'alpha-smoke-adm-value', 'dynamic-snap-value',
    2.0, 1.0, 0.75, 1.25, 2.5, null
);

insert into zk.dynamic_weight_metric_contributions (
    dynamic_run_id, admission_id, metric_id, normalization_rule_id,
    raw_value, normalized_quality, coefficient, weighted_quality_contribution
) values
    ('dynamic-run-abstain', 'alpha-smoke-adm-value', 'icir', 'ICIR_FIXED_V1', 0.75, 0.75, 2.0, 1.50),
    ('dynamic-run-abstain', 'alpha-smoke-adm-value', 'long_leg', 'LONG_LEG_FIXED_V1', 0.075, 0.75, 1.0, 0.75),
    ('dynamic-run-abstain', 'alpha-smoke-adm-value', 'turnover', 'TURNOVER_FIXED_V1', 0.25, 0.75, 1.0, 0.75);

insert into zk.dynamic_weight_insufficient_factors (
    dynamic_run_id, admission_id, reason, snapshot_id
) values (
    'dynamic-run-abstain', 'alpha-smoke-adm-mom', 'MISSING_SNAPSHOT', null
);
commit;

select dynamic_run_id, status, base_gross_exposure, resolved_gross_exposure
from zk.dynamic_weight_runs
where specification_id = 'dynamic-smoke'
order by dynamic_run_id;
