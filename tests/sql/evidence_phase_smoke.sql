\set ON_ERROR_STOP on

insert into zk.evidence_readiness_specs (
  specification_id,definition_version,preregistered_at
) values (
  'real-pit-v1','v1',timestamptz '2026-10-04 10:00:00+00'
);

insert into zk.evidence_readiness_thresholds values
  ('real-pit-v1','v1','PRICES',0.95,now()),
  ('real-pit-v1','v1','FINANCIALS',0.90,now());

insert into zk.source_artifacts (
  artifact_id,source_id,source_url,domain,retrieved_at,
  source_published_at,content_sha256,byte_size,logical_key
) values (
  'artifact-prices','borsa_istanbul','https://www.borsaistanbul.com',
  'PRICES',timestamptz '2026-10-04 12:04:00+00',
  timestamptz '2026-10-04 12:00:00+00',
  repeat('a',64),123,'bist:prices:2026-10-04'
);

insert into zk.pit_dataset_snapshots (
  snapshot_id,specification_id,definition_version,as_of,created_at,
  readiness,manifest_sha256
) values (
  'snapshot-smoke','real-pit-v1','v1',
  timestamptz '2026-10-04 12:00:00+00',
  timestamptz '2026-10-04 12:05:00+00',
  'BLOCKED_WITH_GAPS',repeat('b',64)
);

insert into zk.pit_snapshot_artifacts values
  ('snapshot-smoke','artifact-prices',now());

insert into zk.pit_snapshot_domain_coverage values
  ('snapshot-smoke','PRICES',95,100,1,1,now());

insert into zk.pit_snapshot_gaps values
  ('snapshot-smoke','MISSING_DOMAIN:FINANCIALS',now());

select snapshot_id,readiness,manifest_sha256
from zk.pit_dataset_snapshots
where snapshot_id='snapshot-smoke';
