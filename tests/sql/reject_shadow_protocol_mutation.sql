\set ON_ERROR_STOP on
insert into zk.shadow_protocols (
    protocol_id,definition_version,universe_rule_version,
    alpha_specification_id,alpha_definition_version,
    confidence_specification_id,confidence_definition_version,
    preregistered_at
) values (
    'reject-shadow-mutation','v1','universe-v1',
    'alpha','v1','confidence','v1',
    timestamptz '2026-10-01 00:00:00+00'
);
update zk.shadow_protocols
set universe_rule_version='changed'
where protocol_id='reject-shadow-mutation' and definition_version='v1';
