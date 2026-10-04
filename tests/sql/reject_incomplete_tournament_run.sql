\set ON_ERROR_STOP on
begin;
insert into zk.tournament_runs (
    tournament_run_id, tournament_id, definition_version,
    data_snapshot_id, executed_at
) values (
    'tournament-incomplete-run', 'tournament-smoke', 'v1',
    'snap-6', timestamptz '2026-10-04 01:00:00+00'
);
commit;
