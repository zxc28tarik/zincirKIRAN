\set ON_ERROR_STOP on
insert into zk.production_gate_specs (
    gate_id,definition_version,preregistered_at,
    minimum_shadow_days,minimum_shadow_runs,
    minimum_realized_label_coverage,minimum_mean_ic,
    minimum_net_return_after_costs,maximum_drawdown,
    minimum_liquidity_fit
) values (
    'reject-prod-late','v1',
    timestamptz '2026-10-05 09:00:00+00',
    0,0,0.0,0.0,0.0,1.0,0.0
);
insert into zk.production_gate_evaluations (
    evaluation_id,gate_id,definition_version,evaluated_at,
    decision,review_required,automatic_deployment
) values (
    'reject-prod-late-eval','reject-prod-late','v1',
    timestamptz '2026-10-05 09:00:00+00',
    'RESEARCH_ONLY',true,false
);
