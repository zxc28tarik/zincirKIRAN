\set ON_ERROR_STOP on
insert into zk.confidence_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    confidence_protocol_id, universe_rule_version,
    hypothesis, success_criteria, preregistered_at,
    minimum_weight_coverage, signal_eligibility_threshold, stage
) values (
    'confidence-production-attempt', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    'confidence-protocol-v1', 'universe-v1',
    'candidate-only', 'must remain candidate',
    timestamptz '2026-09-01 00:00:00+00',
    0.75, 0.65, 'PRODUCTION'
);
