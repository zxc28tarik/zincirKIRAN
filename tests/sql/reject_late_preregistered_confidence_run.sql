\set ON_ERROR_STOP on

insert into zk.confidence_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    confidence_protocol_id, universe_rule_version,
    hypothesis, success_criteria, preregistered_at,
    minimum_weight_coverage, signal_eligibility_threshold
) values (
    'confidence-late-spec', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    'confidence-protocol-v1', 'universe-v1',
    'late protocol', 'must fail for past prediction',
    timestamptz '2026-10-05 00:00:00+00',
    0.75, 0.65
);

insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-late-run', 'confidence-late-spec', 'v1',
    'alpha-smoke-run-scored',
    timestamptz '2026-10-04 00:00:00+00',
    0.0, 'NO_SIGNAL_REQUIRED_EVIDENCE', null, 0.0, 0.0, 1.0
);
