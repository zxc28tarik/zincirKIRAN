\set ON_ERROR_STOP on

insert into zk.dynamic_evidence_snapshots (
    snapshot_id, admission_id, evidence_protocol_id,
    window_start, window_end, available_at
) values (
    'dynamic-future-snap', 'alpha-smoke-adm-value', 'rolling-oos-v1',
    timestamptz '2026-09-01 00:00:00+00',
    timestamptz '2026-10-05 00:00:00+00',
    timestamptz '2026-10-05 02:00:00+00'
);

insert into zk.dynamic_evidence_metric_values (snapshot_id, metric_id, raw_value)
values
    ('dynamic-future-snap', 'icir', 0.75),
    ('dynamic-future-snap', 'long_leg', 0.075),
    ('dynamic-future-snap', 'turnover', 0.25);

insert into zk.dynamic_weight_runs (
    dynamic_run_id, specification_id, definition_version, prediction_timestamp,
    status, base_gross_exposure, preliminary_gross_exposure,
    resolved_gross_exposure, gross_rescale_factor
) values (
    'dynamic-future-run', 'dynamic-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_EVIDENCE', 3.0, null, null, null
);

insert into zk.dynamic_weight_factor_results (
    dynamic_run_id, admission_id, snapshot_id, base_weight,
    evidence_coverage, evidence_score, multiplier,
    preliminary_weight, final_weight
) values (
    'dynamic-future-run', 'alpha-smoke-adm-value', 'dynamic-future-snap',
    2.0, 1.0, 0.75, 1.25, 2.5, null
);
