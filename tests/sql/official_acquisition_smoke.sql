\set ON_ERROR_STOP on

insert into zk.official_source_definitions (
  source_id,name,landing_url,official,historical_access_note,runtime_dependency_allowed
) values
  ('kap','KAP','https://kap.org.tr',true,'Public disclosure/search surface.',true),
  ('borsa_istanbul','Borsa Istanbul','https://www.borsaistanbul.com',true,'Public files plus DataStore for broader historical data.',true);

insert into zk.acquisition_attempts (
  acquisition_id,source_id,requested_url,attempted_at,status
) values (
  'acq-smoke','kap','https://kap.org.tr/example',now(),'ACQUIRED'
);

insert into zk.acquired_artifact_receipts (
  acquisition_id,source_id,source_url,retrieved_at,content_sha256,byte_size,media_type
) values (
  'acq-smoke','kap','https://kap.org.tr/example',now(),repeat('a',64),123,'text/html'
);

select acquisition_id,source_id,content_sha256
from zk.acquired_artifact_receipts
where acquisition_id='acq-smoke';
