\set ON_ERROR_STOP on
insert into zk.shadow_protocols (
    protocol_id,definition_version,universe_rule_version,
    alpha_specification_id,alpha_definition_version,
    confidence_specification_id,confidence_definition_version,
    preregistered_at
) values (
    'reject-shadow-decision','v1','universe-v1',
    'alpha','v1','confidence','v1',
    timestamptz '2026-10-01 00:00:00+00'
);
insert into zk.shadow_runs (
    shadow_run_id,protocol_id,definition_version,
    as_of,executed_at,data_snapshot_id,universe_snapshot_id,
    input_receipt_hash,output_receipt_hash
) values (
    'reject-shadow-decision-run','reject-shadow-decision','v1',
    timestamptz '2026-10-04 07:00:00+00',
    timestamptz '2026-10-04 07:01:00+00',
    'data','universe','input','output'
);
insert into zk.shadow_security_decisions (
    shadow_run_id,security_id,decision,alpha_score
) values ('reject-shadow-decision-run','AAA','NO_SIGNAL',0.1);
update zk.shadow_security_decisions
set alpha_score=0.9
where shadow_run_id='reject-shadow-decision-run' and security_id='AAA';
