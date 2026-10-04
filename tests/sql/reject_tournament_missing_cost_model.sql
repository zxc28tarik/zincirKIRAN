\set ON_ERROR_STOP on
begin;
insert into zk.tournament_runs (
    tournament_run_id, tournament_id, definition_version,
    data_snapshot_id, executed_at
) values (
    'tournament-cost-bad-run', 'tournament-smoke', 'v1',
    'snap-2', timestamptz '2026-10-04 01:00:00+00'
);
insert into zk.tournament_fold_metrics (
    tournament_run_id, contender_id, fold_id, metric_id,
    metric_value, sample_size, cost_model_id
) values (
    'tournament-cost-bad-run', 'static', 'fold-1',
    'net_return_after_costs', 0.10, 100, null
);
