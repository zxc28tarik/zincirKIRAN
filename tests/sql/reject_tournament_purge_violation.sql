\set ON_ERROR_STOP on
insert into zk.tournament_specs (
    tournament_id, definition_version, horizon_days,
    universe_rule_version, evaluation_target, hypothesis, success_criteria,
    preregistered_at, purge_days, embargo_days,
    multiple_testing_method, primary_metric_id
) values (
    'tournament-purge-bad', 'v1', 20, 'u', 'target', 'h', 's',
    now(), 3, 0, 'BENJAMINI_HOCHBERG', 'm'
);
insert into zk.tournament_folds (
    tournament_id, definition_version, fold_id,
    train_start, train_end, validation_start, validation_end
) values (
    'tournament-purge-bad', 'v1', 'f1',
    date '2020-01-01', date '2021-12-31',
    date '2022-01-03', date '2022-12-31'
);
