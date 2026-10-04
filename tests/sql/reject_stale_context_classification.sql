\set ON_ERROR_STOP on

insert into zk.context_regime_observations (
    observation_id, dimension_id, context_protocol_id, raw_value,
    window_start, window_end, available_at, source_snapshot_id
) values (
    'context-stale-risk-obs', 'risk_axis', 'context-protocol-v1', 2.0,
    timestamptz '2026-08-01 00:00:00+00',
    timestamptz '2026-09-01 00:00:00+00',
    timestamptz '2026-09-01 01:00:00+00',
    'stale-source'
);

begin;
insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-stale-run', 'context-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_REGIME'
);

insert into zk.context_regime_results (
    context_run_id, dimension_id, availability, observation_id, state_id
) values (
    'context-stale-run', 'risk_axis',
    'CLASSIFIED', 'context-stale-risk-obs', 'state_stressed'
);
