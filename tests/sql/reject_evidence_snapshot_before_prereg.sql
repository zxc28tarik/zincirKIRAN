\set ON_ERROR_STOP on
insert into zk.evidence_readiness_specs values (
 'reject-prereg','v1',timestamptz '2026-10-04 12:00:00+00',now()
);
insert into zk.pit_dataset_snapshots (
 snapshot_id,specification_id,definition_version,as_of,created_at,readiness,manifest_sha256
) values (
 'reject-snapshot','reject-prereg','v1',
 timestamptz '2026-10-04 11:00:00+00',
 timestamptz '2026-10-04 12:00:00+00',
 'BLOCKED_WITH_GAPS',repeat('c',64)
);
