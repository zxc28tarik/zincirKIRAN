\set ON_ERROR_STOP on
insert into zk.context_research_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    context_protocol_id, universe_rule_version, hypothesis, success_criteria,
    preregistered_at, stage
) values (
    'context-production-attempt', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    'context-protocol-v1', 'universe-v1',
    'candidate-only', 'must remain candidate',
    timestamptz '2026-09-01 00:00:00+00',
    'PRODUCTION'
);
