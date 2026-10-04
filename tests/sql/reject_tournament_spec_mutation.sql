\set ON_ERROR_STOP on
update zk.tournament_specs
set purge_days = 99
where tournament_id = 'tournament-smoke' and definition_version = 'v1';
