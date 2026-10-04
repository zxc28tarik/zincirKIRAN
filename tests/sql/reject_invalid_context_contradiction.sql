\set ON_ERROR_STOP on
begin;
insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-bad-contradiction-run', 'context-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00', 'EVALUATED'
);

insert into zk.context_factor_signals (
    context_run_id, admission_id, normalized_signal_value
) values
    ('context-bad-contradiction-run', 'alpha-smoke-adm-value', 0.8),
    ('context-bad-contradiction-run', 'alpha-smoke-adm-mom', -0.6);

insert into zk.context_regime_results (
    context_run_id, dimension_id, availability, observation_id, state_id
) values
    ('context-bad-contradiction-run', 'macro_axis', 'CLASSIFIED', 'context-obs-macro', 'state_high'),
    ('context-bad-contradiction-run', 'risk_axis', 'CLASSIFIED', 'context-obs-risk', 'state_stressed');

insert into zk.context_contradiction_results (
    context_run_id, rule_id, left_signal, right_signal,
    regime_condition_met, is_contradiction
) values (
    'context-bad-contradiction-run', 'value-vs-momentum',
    0.8, -0.6, true, false
);
