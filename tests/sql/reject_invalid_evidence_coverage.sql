\set ON_ERROR_STOP on
insert into zk.evidence_readiness_specs values ('reject-cov','v1',now()-interval '1 day',now());
insert into zk.pit_dataset_snapshots (
 snapshot_id,specification_id,definition_version,as_of,created_at,readiness,manifest_sha256
) values (
 'reject-cov-snap','reject-cov','v1',now()-interval '1 hour',now(),
 'BLOCKED_WITH_GAPS',repeat('d',64)
);
insert into zk.pit_snapshot_domain_coverage values (
 'reject-cov-snap','PRICES',101,100,1,1,now()
);
