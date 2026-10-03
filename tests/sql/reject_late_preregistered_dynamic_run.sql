\set ON_ERROR_STOP on

insert into zk.dynamic_weighting_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    evidence_protocol_id, universe_rule_version, hypothesis, success_criteria,
    preregistered_at,
    minimum_metric_coverage, max_evidence_age_days,
    multiplier_floor, multiplier_ceiling, gross_exposure_policy
) values (
    'dynamic-late-spec', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    'rolling-oos-v1', 'universe-v1',
    'late protocol', 'should be rejected for past prediction',
    timestamptz '2026-10-05 00:00:00+00',
    0.75, 120, 0.5, 1.5, 'NONE'
);

insert into zk.dynamic_evidence_terms (
    specification_id, definition_version, metric_id, normalization_rule_id,
    bad_reference, good_reference, coefficient
) values (
    'dynamic-late-spec', 'v1', 'icir', 'ICIR_FIXED_V1', 0.0, 1.0, 1.0
);

insert into zk.dynamic_weight_runs (
    dynamic_run_id, specification_id, definition_version, prediction_timestamp,
    status, base_gross_exposure, preliminary_gross_exposure,
    resolved_gross_exposure, gross_rescale_factor
) values (
    'dynamic-late-run', 'dynamic-late-spec', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_EVIDENCE', 3.0, null, null, null
);
