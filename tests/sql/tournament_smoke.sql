\set ON_ERROR_STOP on

insert into zk.tournament_specs (
    tournament_id, definition_version, horizon_days,
    universe_rule_version, evaluation_target,
    hypothesis, success_criteria, preregistered_at,
    purge_days, embargo_days, multiple_testing_method,
    primary_metric_id
) values (
    'tournament-smoke', 'v1', 20,
    'universe-v1', 'future_market_relative_total_return',
    'Challengers may improve OOS evidence without hidden leakage.',
    'Review only after robust multi-metric OOS evidence.',
    timestamptz '2026-01-01 00:00:00+00',
    1, 1, 'BENJAMINI_HOCHBERG',
    'net_return_after_costs'
);

insert into zk.tournament_contenders (
    tournament_id, definition_version, contender_id, role,
    artifact_kind, artifact_specification_id,
    artifact_definition_version, rationale
) values
    ('tournament-smoke', 'v1', 'dynamic', 'CHALLENGER',
     'DYNAMIC_ALPHA', 'dynamic-h20', 'v1', 'Dynamic evidence challenger.'),
    ('tournament-smoke', 'v1', 'static', 'CHAMPION',
     'INTERPRETABLE_ALPHA', 'alpha-h20', 'v1', 'Static interpretable champion.');

insert into zk.tournament_folds (
    tournament_id, definition_version, fold_id,
    train_start, train_end, validation_start, validation_end
) values
    ('tournament-smoke', 'v1', 'fold-1',
     date '2020-01-01', date '2021-12-31',
     date '2022-01-03', date '2022-12-30'),
    ('tournament-smoke', 'v1', 'fold-2',
     date '2020-01-01', date '2022-12-30',
     date '2023-01-03', date '2023-12-29'),
    ('tournament-smoke', 'v1', 'fold-3',
     date '2020-01-01', date '2023-12-29',
     date '2024-01-02', date '2024-12-31');

insert into zk.tournament_metric_specs (
    tournament_id, definition_version, metric_id,
    direction, required, requires_cost_model
) values
    ('tournament-smoke', 'v1', 'max_drawdown', 'LOWER_IS_BETTER', true, false),
    ('tournament-smoke', 'v1', 'net_return_after_costs', 'HIGHER_IS_BETTER', true, true),
    ('tournament-smoke', 'v1', 'sharpe', 'HIGHER_IS_BETTER', true, false);

begin;
insert into zk.tournament_runs (
    tournament_run_id, tournament_id, definition_version,
    data_snapshot_id, executed_at
) values (
    'tournament-run-smoke', 'tournament-smoke', 'v1',
    'snapshot-oos-v1', timestamptz '2026-10-04 00:00:00+00'
);

insert into zk.tournament_fold_metrics (
    tournament_run_id, contender_id, fold_id, metric_id,
    metric_value, sample_size, cost_model_id
) values
    ('tournament-run-smoke', 'static', 'fold-1', 'max_drawdown', 0.20, 100, null),
    ('tournament-run-smoke', 'static', 'fold-2', 'max_drawdown', 0.20, 100, null),
    ('tournament-run-smoke', 'static', 'fold-3', 'max_drawdown', 0.20, 100, null),
    ('tournament-run-smoke', 'static', 'fold-1', 'net_return_after_costs', 0.08, 100, 'cost-v1'),
    ('tournament-run-smoke', 'static', 'fold-2', 'net_return_after_costs', 0.10, 100, 'cost-v1'),
    ('tournament-run-smoke', 'static', 'fold-3', 'net_return_after_costs', 0.06, 100, 'cost-v1'),
    ('tournament-run-smoke', 'static', 'fold-1', 'sharpe', 0.80, 100, null),
    ('tournament-run-smoke', 'static', 'fold-2', 'sharpe', 1.00, 100, null),
    ('tournament-run-smoke', 'static', 'fold-3', 'sharpe', 1.20, 100, null),

    ('tournament-run-smoke', 'dynamic', 'fold-1', 'max_drawdown', 0.19, 100, null),
    ('tournament-run-smoke', 'dynamic', 'fold-2', 'max_drawdown', 0.19, 100, null),
    ('tournament-run-smoke', 'dynamic', 'fold-3', 'max_drawdown', 0.19, 100, null),
    ('tournament-run-smoke', 'dynamic', 'fold-1', 'net_return_after_costs', 0.09, 100, 'cost-v1'),
    ('tournament-run-smoke', 'dynamic', 'fold-2', 'net_return_after_costs', null, 0, null),
    ('tournament-run-smoke', 'dynamic', 'fold-3', 'net_return_after_costs', 0.09, 100, 'cost-v1'),
    ('tournament-run-smoke', 'dynamic', 'fold-1', 'sharpe', 0.90, 100, null),
    ('tournament-run-smoke', 'dynamic', 'fold-2', 'sharpe', 1.10, 100, null),
    ('tournament-run-smoke', 'dynamic', 'fold-3', 'sharpe', 1.30, 100, null);

insert into zk.tournament_aggregate_metrics (
    tournament_run_id, contender_id, metric_id,
    valid_folds, total_folds, mean_value, dispersion
) values
    ('tournament-run-smoke', 'dynamic', 'max_drawdown', 3, 3, 0.19, 0.0),
    ('tournament-run-smoke', 'dynamic', 'net_return_after_costs', 2, 3, 0.09, 0.0),
    ('tournament-run-smoke', 'dynamic', 'sharpe', 3, 3, 1.10, 0.20),
    ('tournament-run-smoke', 'static', 'max_drawdown', 3, 3, 0.20, 0.0),
    ('tournament-run-smoke', 'static', 'net_return_after_costs', 3, 3, 0.08, 0.02),
    ('tournament-run-smoke', 'static', 'sharpe', 3, 3, 1.00, 0.20);

insert into zk.tournament_paired_differences (
    tournament_run_id, challenger_id, metric_id,
    paired_folds, mean_difference_vs_champion
) values
    ('tournament-run-smoke', 'dynamic', 'max_drawdown', 3, 0.01),
    ('tournament-run-smoke', 'dynamic', 'net_return_after_costs', 2, 0.02),
    ('tournament-run-smoke', 'dynamic', 'sharpe', 3, 0.10);

insert into zk.tournament_multiple_testing (
    tournament_run_id, contender_id, metric_id, pvalue, qvalue
) values
    ('tournament-run-smoke', 'dynamic', 'max_drawdown', 0.20, 0.20),
    ('tournament-run-smoke', 'dynamic', 'net_return_after_costs', 0.01, 0.03),
    ('tournament-run-smoke', 'dynamic', 'sharpe', 0.04, 0.06);

insert into zk.tournament_outcomes (
    tournament_run_id, champion_id, decision,
    automatic_promotion, review_required, primary_metric_id
) values (
    'tournament-run-smoke', 'static',
    'RETAIN_CHAMPION_REVIEW_REQUIRED',
    false, true, 'net_return_after_costs'
);
commit;

select tournament_run_id, champion_id, decision, automatic_promotion, review_required
from zk.tournament_outcomes
where tournament_run_id = 'tournament-run-smoke';
