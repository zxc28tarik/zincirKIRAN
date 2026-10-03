\set ON_ERROR_STOP on

insert into zk.decorrelation_runs (
    run_id, data_snapshot_id, universe_rule_version, correlation_method,
    minimum_overlap, absolute_threshold, residualization_include_intercept,
    preregistered_at
) values (
    'decor-immutable-v1', 'snapshot-v1', 'universe-v1', 'PEARSON',
    20, 0.75, false, now()
);

update zk.decorrelation_runs
set absolute_threshold = 0.95
where run_id = 'decor-immutable-v1';
