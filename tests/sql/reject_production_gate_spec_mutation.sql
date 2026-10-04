\set ON_ERROR_STOP on
insert into zk.production_gate_specs (
    gate_id,definition_version,preregistered_at,
    minimum_shadow_days,minimum_shadow_runs,
    minimum_realized_label_coverage,minimum_mean_ic,
    minimum_net_return_after_costs,maximum_drawdown,
    minimum_liquidity_fit
) values (
    'reject-prod-mutation','v1',
    timestamptz '2026-10-04 09:00:00+00',
    60,40,0.8,0.02,0.01,0.25,0.70
);
update zk.production_gate_specs
set minimum_shadow_days=30
where gate_id='reject-prod-mutation' and definition_version='v1';
