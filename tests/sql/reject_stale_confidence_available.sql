\set ON_ERROR_STOP on

insert into zk.confidence_observations (
    observation_id, security_id, dimension_id, confidence_protocol_id,
    raw_value, window_start, window_end, available_at, source_reference
) values (
    'confidence-stale-obs',
    '70000000-0000-0000-0000-000000000002'::uuid,
    'freshness', 'confidence-protocol-v1', 0.90,
    timestamptz '2026-09-01 00:00:00+00',
    timestamptz '2026-09-20 00:00:00+00',
    timestamptz '2026-09-20 01:00:00+00',
    'stale-source'
);

begin;
insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-stale-run', 'confidence-smoke', 'v1',
    'alpha-smoke-run-scored',
    timestamptz '2026-10-04 00:00:00+00',
    0.0, 'NO_SIGNAL_REQUIRED_EVIDENCE', null, 0.0, 0.0, 8.0
);

insert into zk.confidence_dimension_results (
    confidence_run_id, dimension_id, availability, observation_id,
    raw_value, normalized_quality, weight, weighted_contribution,
    hard_floor, hard_floor_pass, age_days
) values (
    'confidence-stale-run', 'freshness', 'AVAILABLE',
    'confidence-stale-obs', 0.90, 0.90, 1.0, 0.90, 0.50, true, 14.0
);
