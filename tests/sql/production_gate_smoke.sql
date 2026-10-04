\set ON_ERROR_STOP on

insert into zk.production_gate_specs (
    gate_id, definition_version, preregistered_at,
    minimum_shadow_days, minimum_shadow_runs,
    minimum_realized_label_coverage, minimum_mean_ic,
    minimum_net_return_after_costs, maximum_drawdown,
    minimum_liquidity_fit
) values (
    'prod-gate-v1','v1',
    timestamptz '2026-10-04 09:00:00+00',
    60,40,0.80,0.02,0.01,0.25,0.70
);

insert into zk.production_gate_evaluations (
    evaluation_id,gate_id,definition_version,evaluated_at,
    tournament_run_id,shadow_protocol_id,shadow_days,shadow_runs,
    realized_label_coverage,mean_ic,net_return_after_costs,max_drawdown,
    liquidity_fit,replay_integrity,pit_integrity,cost_model_present,
    capacity_evidence_present,decision,review_required,automatic_deployment
) values (
    'prod-eval-smoke','prod-gate-v1','v1',
    timestamptz '2026-12-31 09:00:00+00',
    'tournament-run-1','shadow-v1',90,65,
    0.90,0.04,0.03,0.18,0.90,
    true,true,true,true,
    'PRODUCTION_ELIGIBLE_REVIEW_REQUIRED',true,false
);

select evaluation_id,decision,review_required,automatic_deployment
from zk.production_gate_evaluations
where evaluation_id='prod-eval-smoke';
