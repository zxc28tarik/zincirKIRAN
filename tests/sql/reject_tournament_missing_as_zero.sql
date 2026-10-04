begin;
insert into zk.tournament_runs (
    tournament_run_id, tournament_id, definition_version,
    data_snapshot_id, executed_at
) values (
    'tournament-missing-zero-run', 'tournament-smoke', 'v1',
    'snap-3', timestamptz '2026-10-04 01:00:00+00'
);
insert into zk.tournament_fold_metrics (
    tournament_run_id, contender_id, fold_id, metric_id,
    metric_value, sample_size, cost_model_id
)
select 'tournament-missing-zero-run', contender_id, fold_id, metric_id,
       metric_value, sample_size, cost_model_id
from zk.tournament_fold_metrics
where tournament_run_id = 'tournament-run-smoke';

insert into zk.tournament_aggregate_metrics (
    tournament_run_id, contender_id, metric_id,
    valid_folds, total_folds, mean_value, dispersion
)
select 'tournament-missing-zero-run', contender_id, metric_id,
       valid_folds, total_folds, mean_value, dispersion
from zk.tournament_aggregate_metrics
where tournament_run_id = 'tournament-run-smoke'
  and not (contender_id = 'dynamic' and metric_id = 'net_return_after_costs');

insert into zk.tournament_aggregate_metrics (
    tournament_run_id, contender_id, metric_id,
    valid_folds, total_folds, mean_value, dispersion
) values (
    'tournament-missing-zero-run', 'dynamic',
    'net_return_after_costs', 3, 3, 0.06, 0.0519615242270663
);

insert into zk.tournament_paired_differences (
    tournament_run_id, challenger_id, metric_id,
    paired_folds, mean_difference_vs_champion
)
select 'tournament-missing-zero-run', challenger_id, metric_id,
       paired_folds, mean_difference_vs_champion
from zk.tournament_paired_differences
where tournament_run_id = 'tournament-run-smoke';

insert into zk.tournament_multiple_testing (
    tournament_run_id, contender_id, metric_id, pvalue, qvalue
)
select 'tournament-missing-zero-run', contender_id, metric_id, pvalue, qvalue
from zk.tournament_multiple_testing
where tournament_run_id = 'tournament-run-smoke';

insert into zk.tournament_outcomes (
    tournament_run_id, champion_id, decision,
    automatic_promotion, review_required, primary_metric_id
)
select 'tournament-missing-zero-run', champion_id, decision,
       automatic_promotion, review_required, primary_metric_id
from zk.tournament_outcomes
where tournament_run_id = 'tournament-run-smoke';
commit;
