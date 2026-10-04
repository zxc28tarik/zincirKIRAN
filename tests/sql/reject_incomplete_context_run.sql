\set ON_ERROR_STOP on
begin;
insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-incomplete-run', 'context-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00', 'EVALUATED'
);

insert into zk.context_factor_signals (
    context_run_id, admission_id, normalized_signal_value
) values
    ('context-incomplete-run', 'alpha-smoke-adm-value', 0.8),
    ('context-incomplete-run', 'alpha-smoke-adm-mom', -0.6);

insert into zk.context_regime_results (
    context_run_id, dimension_id, availability, observation_id, state_id
) values
    ('context-incomplete-run', 'macro_axis', 'CLASSIFIED', 'context-obs-macro', 'state_high'),
    ('context-incomplete-run', 'risk_axis', 'CLASSIFIED', 'context-obs-risk', 'state_stressed');
commit;
