\set ON_ERROR_STOP on
insert into zk.tournament_specs (
    tournament_id, definition_version, horizon_days,
    universe_rule_version, evaluation_target, hypothesis, success_criteria,
    preregistered_at, purge_days, embargo_days,
    multiple_testing_method, primary_metric_id
) values (
    'tournament-late', 'v1', 20, 'u', 'target', 'h', 's',
    timestamptz '2026-10-05 00:00:00+00',
    0, 0, 'BENJAMINI_HOCHBERG', 'm'
);
insert into zk.tournament_runs (
    tournament_run_id, tournament_id, definition_version,
    data_snapshot_id, executed_at
) values (
    'tournament-late-run', 'tournament-late', 'v1',
    'snap', timestamptz '2026-10-04 00:00:00+00'
);
