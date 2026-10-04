\set ON_ERROR_STOP on
begin;
insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-bad-arithmetic-run', 'confidence-smoke', 'v1',
    'alpha-smoke-run-scored',
    timestamptz '2026-10-04 00:00:00+00',
    0.0, 'NO_SIGNAL_REQUIRED_EVIDENCE', null, 0.0, 0.0, 8.0
);

insert into zk.confidence_dimension_results (
    confidence_run_id, dimension_id, availability, observation_id,
    raw_value, normalized_quality, weight, weighted_contribution,
    hard_floor, hard_floor_pass, age_days
) values (
    'confidence-bad-arithmetic-run', 'data_coverage', 'AVAILABLE',
    'confidence-obs-data', 0.95, 0.70, 2.0, 1.40, 0.60, true, 1.0
);
