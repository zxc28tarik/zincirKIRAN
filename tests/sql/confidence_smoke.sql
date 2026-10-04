\set ON_ERROR_STOP on

insert into zk.confidence_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    confidence_protocol_id, universe_rule_version,
    hypothesis, success_criteria, preregistered_at,
    minimum_weight_coverage, signal_eligibility_threshold
) values (
    'confidence-smoke', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    'confidence-protocol-v1', 'universe-v1',
    'Evidence quality should gate whether Alpha is actionable.',
    'Reject fragile signals without modifying Alpha.',
    timestamptz '2026-09-01 00:00:00+00',
    0.75, 0.65
);

insert into zk.confidence_dimensions (
    specification_id, definition_version, dimension_id, kind, required,
    max_age_days, weight, bad_reference, good_reference, hard_floor
) values
    ('confidence-smoke', 'v1', 'data_coverage', 'DATA_COVERAGE', true, 5, 2.0, 0.50, 1.00, 0.60),
    ('confidence-smoke', 'v1', 'factor_evidence', 'FACTOR_EVIDENCE', true, 30, 2.0, 0.00, 1.00, 0.40),
    ('confidence-smoke', 'v1', 'freshness', 'FRESHNESS', true, 5, 1.0, 0.00, 1.00, 0.50),
    ('confidence-smoke', 'v1', 'liquidity', 'LIQUIDITY', false, 5, 1.0, 0.00, 1.00, 0.30),
    ('confidence-smoke', 'v1', 'model_agreement', 'MODEL_AGREEMENT', false, 5, 1.0, 0.00, 1.00, null),
    ('confidence-smoke', 'v1', 'pit_certainty', 'PIT_CERTAINTY', true, 30, 1.0, 0.00, 1.00, 0.70);

insert into zk.confidence_observations (
    observation_id, security_id, dimension_id, confidence_protocol_id,
    raw_value, window_start, window_end, available_at, source_reference
) values
    ('confidence-obs-data', '70000000-0000-0000-0000-000000000002'::uuid, 'data_coverage', 'confidence-protocol-v1', 0.95,
     timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'source-data'),
    ('confidence-obs-factor', '70000000-0000-0000-0000-000000000002'::uuid, 'factor_evidence', 'confidence-protocol-v1', 0.80,
     timestamptz '2026-09-01 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'source-factor'),
    ('confidence-obs-fresh', '70000000-0000-0000-0000-000000000002'::uuid, 'freshness', 'confidence-protocol-v1', 0.90,
     timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'source-fresh'),
    ('confidence-obs-liquidity', '70000000-0000-0000-0000-000000000002'::uuid, 'liquidity', 'confidence-protocol-v1', 0.80,
     timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'source-liquidity'),
    ('confidence-obs-model', '70000000-0000-0000-0000-000000000002'::uuid, 'model_agreement', 'confidence-protocol-v1', 0.75,
     timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'source-model'),
    ('confidence-obs-pit', '70000000-0000-0000-0000-000000000002'::uuid, 'pit_certainty', 'confidence-protocol-v1', 0.95,
     timestamptz '2026-09-01 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'source-pit');

begin;
insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-run-eligible', 'confidence-smoke', 'v1',
    'alpha-smoke-run-scored',
    timestamptz '2026-10-04 00:00:00+00',
    0.0, 'SIGNAL_ELIGIBLE', 0.85, 1.0, 8.0, 8.0
);

insert into zk.confidence_dimension_results (
    confidence_run_id, dimension_id, availability, observation_id,
    raw_value, normalized_quality, weight, weighted_contribution,
    hard_floor, hard_floor_pass, age_days
) values
    ('confidence-run-eligible', 'data_coverage', 'AVAILABLE', 'confidence-obs-data', 0.95, 0.90, 2.0, 1.80, 0.60, true, 1.0),
    ('confidence-run-eligible', 'factor_evidence', 'AVAILABLE', 'confidence-obs-factor', 0.80, 0.80, 2.0, 1.60, 0.40, true, 1.0),
    ('confidence-run-eligible', 'freshness', 'AVAILABLE', 'confidence-obs-fresh', 0.90, 0.90, 1.0, 0.90, 0.50, true, 1.0),
    ('confidence-run-eligible', 'liquidity', 'AVAILABLE', 'confidence-obs-liquidity', 0.80, 0.80, 1.0, 0.80, 0.30, true, 1.0),
    ('confidence-run-eligible', 'model_agreement', 'AVAILABLE', 'confidence-obs-model', 0.75, 0.75, 1.0, 0.75, null, null, 1.0),
    ('confidence-run-eligible', 'pit_certainty', 'AVAILABLE', 'confidence-obs-pit', 0.95, 0.95, 1.0, 0.95, 0.70, true, 1.0);
commit;

begin;
insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-run-required-missing', 'confidence-smoke', 'v1',
    'alpha-smoke-run-scored',
    timestamptz '2026-10-04 00:00:00+00',
    0.0, 'NO_SIGNAL_REQUIRED_EVIDENCE', null, 0.875, 7.0, 8.0
);

insert into zk.confidence_dimension_results (
    confidence_run_id, dimension_id, availability, observation_id,
    raw_value, normalized_quality, weight, weighted_contribution,
    hard_floor, hard_floor_pass, age_days
) values
    ('confidence-run-required-missing', 'data_coverage', 'AVAILABLE', 'confidence-obs-data', 0.95, 0.90, 2.0, 1.80, 0.60, true, 1.0),
    ('confidence-run-required-missing', 'factor_evidence', 'AVAILABLE', 'confidence-obs-factor', 0.80, 0.80, 2.0, 1.60, 0.40, true, 1.0),
    ('confidence-run-required-missing', 'freshness', 'AVAILABLE', 'confidence-obs-fresh', 0.90, 0.90, 1.0, 0.90, 0.50, true, 1.0),
    ('confidence-run-required-missing', 'liquidity', 'AVAILABLE', 'confidence-obs-liquidity', 0.80, 0.80, 1.0, 0.80, 0.30, true, 1.0),
    ('confidence-run-required-missing', 'model_agreement', 'AVAILABLE', 'confidence-obs-model', 0.75, 0.75, 1.0, 0.75, null, null, 1.0),
    ('confidence-run-required-missing', 'pit_certainty', 'MISSING', null, null, null, 1.0, null, 0.70, null, null);

insert into zk.confidence_abstention_reasons (
    confidence_run_id, reason_code, dimension_id
) values (
    'confidence-run-required-missing', 'REQUIRED_EVIDENCE', 'pit_certainty'
);
commit;

begin;
insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-run-alpha-unavailable', 'confidence-smoke', 'v1',
    'alpha-smoke-run-abstain',
    timestamptz '2026-10-04 00:00:00+00',
    null, 'NO_SIGNAL_ALPHA_UNAVAILABLE', null, 1.0, 8.0, 8.0
);

insert into zk.confidence_dimension_results (
    confidence_run_id, dimension_id, availability, observation_id,
    raw_value, normalized_quality, weight, weighted_contribution,
    hard_floor, hard_floor_pass, age_days
) values
    ('confidence-run-alpha-unavailable', 'data_coverage', 'AVAILABLE', 'confidence-obs-data', 0.95, 0.90, 2.0, 1.80, 0.60, true, 1.0),
    ('confidence-run-alpha-unavailable', 'factor_evidence', 'AVAILABLE', 'confidence-obs-factor', 0.80, 0.80, 2.0, 1.60, 0.40, true, 1.0),
    ('confidence-run-alpha-unavailable', 'freshness', 'AVAILABLE', 'confidence-obs-fresh', 0.90, 0.90, 1.0, 0.90, 0.50, true, 1.0),
    ('confidence-run-alpha-unavailable', 'liquidity', 'AVAILABLE', 'confidence-obs-liquidity', 0.80, 0.80, 1.0, 0.80, 0.30, true, 1.0),
    ('confidence-run-alpha-unavailable', 'model_agreement', 'AVAILABLE', 'confidence-obs-model', 0.75, 0.75, 1.0, 0.75, null, null, 1.0),
    ('confidence-run-alpha-unavailable', 'pit_certainty', 'AVAILABLE', 'confidence-obs-pit', 0.95, 0.95, 1.0, 0.95, 0.70, true, 1.0);

insert into zk.confidence_abstention_reasons (
    confidence_run_id, reason_code, dimension_id
) values (
    'confidence-run-alpha-unavailable', 'ALPHA_UNAVAILABLE', null
);
commit;

select confidence_run_id, decision, confidence_score, evidence_weight_coverage
from zk.confidence_runs
where specification_id = 'confidence-smoke'
order by confidence_run_id;
