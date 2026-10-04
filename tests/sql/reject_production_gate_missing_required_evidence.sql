\set ON_ERROR_STOP on
insert into zk.production_gate_specs (
    gate_id,definition_version,preregistered_at,
    minimum_shadow_days,minimum_shadow_runs,
    minimum_realized_label_coverage,minimum_mean_ic,
    minimum_net_return_after_costs,maximum_drawdown,
    minimum_liquidity_fit
) values (
    'reject-prod-missing','v1',
    timestamptz '2026-10-04 09:00:00+00',
    0,0,0.0,0.0,0.0,1.0,0.0
);
insert into zk.production_gate_evaluations (
    evaluation_id,gate_id,definition_version,evaluated_at,
    tournament_run_id,shadow_protocol_id,shadow_days,shadow_runs,
    realized_label_coverage,mean_ic,net_return_after_costs,max_drawdown,
    liquidity_fit,replay_integrity,pit_integrity,cost_model_present,
    capacity_evidence_present,decision,review_required,automatic_deployment
) values (
    'reject-prod-missing-eval','reject-prod-missing','v1',
    timestamptz '2026-10-05 09:00:00+00',
    null,'shadow-v1',1,1,1.0,0.1,0.1,0.1,1.0,
    true,true,true,true,
    'PRODUCTION_ELIGIBLE_REVIEW_REQUIRED',true,false
);
