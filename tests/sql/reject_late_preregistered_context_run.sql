\set ON_ERROR_STOP on

insert into zk.context_research_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    context_protocol_id, universe_rule_version, hypothesis, success_criteria,
    preregistered_at
) values (
    'context-late-spec', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    'context-protocol-v1', 'universe-v1',
    'late protocol', 'must fail for past prediction',
    timestamptz '2026-10-05 00:00:00+00'
);

insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-late-run', 'context-late-spec', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_REGIME'
);
