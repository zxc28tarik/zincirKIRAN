\set ON_ERROR_STOP on

insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-alpha-mismatch-run', 'confidence-smoke', 'v1',
    'alpha-smoke-run-scored',
    timestamptz '2026-10-04 00:00:00+00',
    0.123, 'NO_SIGNAL_REQUIRED_EVIDENCE', null, 0.0, 0.0, 8.0
);
