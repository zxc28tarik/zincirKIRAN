\set ON_ERROR_STOP on
insert into zk.shadow_protocols (
    protocol_id,definition_version,universe_rule_version,
    alpha_specification_id,alpha_definition_version,
    confidence_specification_id,confidence_definition_version,
    preregistered_at
) values (
    'reject-shadow-horizon','v1','universe-v1',
    'alpha','v1','confidence','v1',
    timestamptz '2026-10-01 00:00:00+00'
);
insert into zk.shadow_protocol_horizons values
    ('reject-shadow-horizon','v1',20,now());
insert into zk.shadow_runs (
    shadow_run_id,protocol_id,definition_version,
    as_of,executed_at,data_snapshot_id,universe_snapshot_id,
    input_receipt_hash,output_receipt_hash
) values (
    'reject-shadow-horizon-run','reject-shadow-horizon','v1',
    timestamptz '2026-10-04 07:00:00+00',
    timestamptz '2026-10-04 07:01:00+00',
    'data','universe','input','output'
);
insert into zk.shadow_security_decisions (
    shadow_run_id,security_id,decision
) values ('reject-shadow-horizon-run','AAA','NO_SIGNAL');
insert into zk.shadow_realized_labels (
    shadow_run_id,security_id,horizon_days,label_available_at,
    market_relative_total_return
) values (
    'reject-shadow-horizon-run','AAA',60,
    timestamptz '2027-01-01 07:00:00+00',0.01
);
