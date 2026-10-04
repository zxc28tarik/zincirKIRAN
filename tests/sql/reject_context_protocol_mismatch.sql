\set ON_ERROR_STOP on

insert into zk.context_regime_observations (
    observation_id, dimension_id, context_protocol_id, raw_value,
    window_start, window_end, available_at, source_snapshot_id
) values (
    'context-wrong-protocol-obs', 'macro_axis', 'post-hoc-protocol', 1.0,
    timestamptz '2026-09-01 00:00:00+00',
    timestamptz '2026-10-03 00:00:00+00',
    timestamptz '2026-10-03 01:00:00+00',
    'wrong-protocol-source'
);

begin;
insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-wrong-protocol-run', 'context-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_REGIME'
);

insert into zk.context_regime_results (
    context_run_id, dimension_id, availability, observation_id, state_id
) values (
    'context-wrong-protocol-run', 'macro_axis',
    'CLASSIFIED', 'context-wrong-protocol-obs', 'state_high'
);
