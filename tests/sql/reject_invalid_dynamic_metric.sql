\set ON_ERROR_STOP on

insert into zk.dynamic_weight_runs (
    dynamic_run_id, specification_id, definition_version, prediction_timestamp,
    status, base_gross_exposure, preliminary_gross_exposure,
    resolved_gross_exposure, gross_rescale_factor
) values (
    'dynamic-bad-metric-run', 'dynamic-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_EVIDENCE', 3.0, null, null, null
);

insert into zk.dynamic_weight_factor_results (
    dynamic_run_id, admission_id, snapshot_id, base_weight,
    evidence_coverage, evidence_score, multiplier,
    preliminary_weight, final_weight
) values (
    'dynamic-bad-metric-run', 'alpha-smoke-adm-value', 'dynamic-snap-value',
    2.0, 1.0, 0.75, 1.25, 2.5, null
);

insert into zk.dynamic_weight_metric_contributions (
    dynamic_run_id, admission_id, metric_id, normalization_rule_id,
    raw_value, normalized_quality, coefficient, weighted_quality_contribution
) values (
    'dynamic-bad-metric-run', 'alpha-smoke-adm-value',
    'icir', 'WRONG_NORMALIZATION', 0.75, 0.75, 2.0, 1.50
);
