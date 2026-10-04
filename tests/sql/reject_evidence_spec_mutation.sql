\set ON_ERROR_STOP on
insert into zk.evidence_readiness_specs values ('reject-spec','v1',now()-interval '1 day',now());
update zk.evidence_readiness_specs set definition_version='v2'
where specification_id='reject-spec' and definition_version='v1';
