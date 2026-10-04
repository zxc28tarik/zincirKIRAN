\set ON_ERROR_STOP on
begin;
insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values (
    'confidence-wrong-decision-run', 'confidence-smoke', 'v1',
    'alpha-smoke-run-scored',
    timestamptz '2026-10-04 00:00:00+00',
    0.0, 'SIGNAL_ELIGIBLE', 0.85, 0.875, 7.0, 8.0
);

insert into zk.confidence_dimension_results (
    confidence_run_id, dimension_id, availability, observation_id,
    raw_value, normalized_quality, weight, weighted_contribution,
    hard_floor, hard_floor_pass, age_days
) values
    ('confidence-wrong-decision-run', 'data_coverage', 'AVAILABLE', 'confidence-obs-data', 0.95, 0.90, 2.0, 1.80, 0.60, true, 1.0),
    ('confidence-wrong-decision-run', 'factor_evidence', 'AVAILABLE', 'confidence-obs-factor', 0.80, 0.80, 2.0, 1.60, 0.40, true, 1.0),
    ('confidence-wrong-decision-run', 'freshness', 'AVAILABLE', 'confidence-obs-fresh', 0.90, 0.90, 1.0, 0.90, 0.50, true, 1.0),
    ('confidence-wrong-decision-run', 'liquidity', 'AVAILABLE', 'confidence-obs-liquidity', 0.80, 0.80, 1.0, 0.80, 0.30, true, 1.0),
    ('confidence-wrong-decision-run', 'model_agreement', 'AVAILABLE', 'confidence-obs-model', 0.75, 0.75, 1.0, 0.75, null, null, 1.0),
    ('confidence-wrong-decision-run', 'pit_certainty', 'MISSING', null, null, null, 1.0, null, 0.70, null, null);
commit;
