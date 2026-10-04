\set ON_ERROR_STOP on
insert into zk.tournament_metric_specs (
    tournament_id, definition_version, metric_id,
    direction, required, requires_cost_model
) values (
    'tournament-smoke', 'v1', 'post_hoc_metric',
    'HIGHER_IS_BETTER', false, false
);
