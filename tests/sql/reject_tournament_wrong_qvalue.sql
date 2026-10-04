begin;
insert into zk.tournament_runs (
    tournament_run_id, tournament_id, definition_version,
    data_snapshot_id, executed_at
) values (
    'tournament-q-bad-run', 'tournament-smoke', 'v1',
    'snap-5', timestamptz '2026-10-04 01:00:00+00'
);

insert into zk.tournament_fold_metrics (
    tournament_run_id, contender_id, fold_id, metric_id,
    metric_value, sample_size, cost_model_id
)
select 'tournament-q-bad-run', contender_id, fold_id, metric_id,
       metric_value, sample_size, cost_model_id
from zk.tournament_fold_metrics
where tournament_run_id = 'tournament-run-smoke';

insert into zk.tournament_aggregate_metrics (
    tournament_run_id, contender_id, metric_id,
    valid_folds, total_folds, mean_value, dispersion
)
select 'tournament-q-bad-run', contender_id, metric_id,
       valid_folds, total_folds, mean_value, dispersion
from zk.tournament_aggregate_metrics
where tournament_run_id = 'tournament-run-smoke';

insert into zk.tournament_paired_differences (
    tournament_run_id, challenger_id, metric_id,
    paired_folds, mean_difference_vs_champion
)
select 'tournament-q-bad-run', challenger_id, metric_id,
       paired_folds, mean_difference_vs_champion
from zk.tournament_paired_differences
where tournament_run_id = 'tournament-run-smoke';

insert into zk.tournament_multiple_testing (
    tournament_run_id, contender_id, metric_id, pvalue, qvalue
) values
    ('tournament-q-bad-run', 'dynamic', 'max_drawdown', 0.20, 0.20),
    ('tournament-q-bad-run', 'dynamic', 'net_return_after_costs', 0.01, 0.01),
    ('tournament-q-bad-run', 'dynamic', 'sharpe', 0.04, 0.04);

insert into zk.tournament_outcomes (
    tournament_run_id, champion_id, decision,
    automatic_promotion, review_required, primary_metric_id
)
select 'tournament-q-bad-run', champion_id, decision,
       automatic_promotion, review_required, primary_metric_id
from zk.tournament_outcomes
where tournament_run_id = 'tournament-run-smoke';
commit;
