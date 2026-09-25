\set ON_ERROR_STOP on

insert into zk.baseline_definitions (
    baseline_id, definition_version, formula, baseline_role
) values (
    'EQUAL_WEIGHT', 'missing-meta-v1', '1/N', 'COMPARATOR'
);

insert into zk.baseline_runs (
    baseline_id, definition_version, horizon_days,
    data_snapshot_id, universe_rule_version, rebalance_specification
) values (
    'EQUAL_WEIGHT', 'missing-meta-v1', 60,
    '', 'universe-v1', 'rebalance-v1'
);
