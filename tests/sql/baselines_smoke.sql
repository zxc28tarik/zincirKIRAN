\set ON_ERROR_STOP on

insert into zk.baseline_definitions (
    baseline_id, definition_version, formula, baseline_role
) values (
    'EQUAL_WEIGHT', 'smoke-v1', '1/N over PIT investable universe', 'COMPARATOR'
);

insert into zk.baseline_definitions (
    baseline_id, definition_version, formula, baseline_role
) values (
    'TOTAL_RASYO', 'smoke-v1', 'failed historical reference only', 'FAILED_REFERENCE'
);

insert into zk.baseline_runs (
    baseline_id, definition_version, horizon_days,
    data_snapshot_id, universe_rule_version, rebalance_specification
) values (
    'EQUAL_WEIGHT', 'smoke-v1', 20,
    'snapshot-smoke', 'universe-v1', 'explicit-smoke-rebalance'
);

select baseline_id, definition_version, horizon_days
from zk.baseline_runs
where data_snapshot_id = 'snapshot-smoke';
