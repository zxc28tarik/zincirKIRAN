\set ON_ERROR_STOP on
insert into zk.context_regime_state_rules (
    specification_id, definition_version, dimension_id, state_id,
    lower_inclusive, upper_exclusive
) values (
    'context-smoke', 'v1', 'macro_axis', 'overlap-state',
    -1.0, 1.0
);
