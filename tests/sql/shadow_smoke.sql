\set ON_ERROR_STOP on

insert into zk.shadow_protocols (
    protocol_id, definition_version, universe_rule_version,
    alpha_specification_id, alpha_definition_version,
    confidence_specification_id, confidence_definition_version,
    ml_challenger_id, ml_definition_version, preregistered_at
) values (
    'shadow-v1','v1','universe-v1',
    'alpha-h20','v1',
    'confidence-h20','v1',
    'ridge-h20-v1','v1',
    timestamptz '2026-10-01 00:00:00+00'
);

insert into zk.shadow_protocol_horizons values
    ('shadow-v1','v1',20,now()),
    ('shadow-v1','v1',60,now());

insert into zk.shadow_runs (
    shadow_run_id, protocol_id, definition_version,
    as_of, executed_at, data_snapshot_id, universe_snapshot_id,
    input_receipt_hash, output_receipt_hash
) values (
    'shadow-run-smoke','shadow-v1','v1',
    timestamptz '2026-10-04 07:00:00+00',
    timestamptz '2026-10-04 07:01:00+00',
    'data-snapshot-1','universe-snapshot-1',
    'input-hash','output-hash'
);

insert into zk.shadow_input_provenance values
    ('shadow-run-smoke','alpha_run_id','alpha-1',now()),
    ('shadow-run-smoke','confidence_run_id','confidence-1',now()),
    ('shadow-run-smoke','ml_fit_id','ml-fit-1',now());

insert into zk.shadow_security_decisions (
    shadow_run_id,security_id,decision,
    alpha_score,confidence_score,ml_score,portfolio_target_weight
) values
    ('shadow-run-smoke','AAA','SIGNAL_ELIGIBLE',0.8,0.9,0.7,0.05),
    ('shadow-run-smoke','BBB','NO_SIGNAL',0.1,0.2,-0.1,null);

insert into zk.shadow_decision_reasons values
    ('shadow-run-smoke','BBB','LOW_CONFIDENCE',now());

insert into zk.shadow_realized_labels (
    shadow_run_id,security_id,horizon_days,
    label_available_at,market_relative_total_return
) values (
    'shadow-run-smoke','AAA',20,
    timestamptz '2026-10-24 07:00:00+00',0.04
);

select shadow_run_id,security_id,decision,portfolio_target_weight
from zk.shadow_security_decisions
where shadow_run_id='shadow-run-smoke'
order by security_id;
