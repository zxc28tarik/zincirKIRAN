\set ON_ERROR_STOP on

insert into zk.procurement_specs (
  specification_id,definition_version,preregistered_at,purchase_authorized
) values (
  'first-actual-dataset-v1','v1',
  timestamptz '2026-10-04 14:05:00+00',false
);

insert into zk.procurement_routes (
  specification_id,definition_version,domain,route_id,source_id,source_surface,
  access_class,pit_suitability,canonical,status,rationale
) values
  ('first-actual-dataset-v1','v1','PRICES','prices-bist-datastore','borsa_istanbul',
   'Borsa Istanbul DataStore historical Equity Market data','PAID_OFFICIAL','CANONICAL',true,
   'BLOCKED_PENDING_ACCESS','Official historical route.'),
  ('first-actual-dataset-v1','v1','VOLUME','volume-bist-datastore','borsa_istanbul',
   'Borsa Istanbul DataStore historical Equity Market data','PAID_OFFICIAL','CANONICAL',true,
   'BLOCKED_PENDING_ACCESS','Official historical route.'),
  ('first-actual-dataset-v1','v1','FINANCIALS','financials-kap-original-reports','kap',
   'Original KAP financial-report disclosures and attachments','FREE_PUBLIC','CANONICAL',true,
   'BLOCKED_PENDING_EXPORT','Original filings preserve PIT publication provenance.'),
  ('first-actual-dataset-v1','v1','PUBLICATION_TIMESTAMPS','publication-time-kap','kap',
   'KAP disclosure timestamps','FREE_PUBLIC','CANONICAL',true,
   'ROUTE_LOCKED','Canonical publication timestamp.'),
  ('first-actual-dataset-v1','v1','CORPORATE_ACTIONS','corporate-actions-kap-primary','kap',
   'Original KAP corporate-action disclosures','FREE_PUBLIC','CANONICAL',true,
   'ROUTE_LOCKED','Canonical corporate-action source.'),
  ('first-actual-dataset-v1','v1','UNIVERSE_HISTORY','universe-bist-reference','borsa_istanbul',
   'Borsa Istanbul official listing/reference files','FREE_PUBLIC','CANONICAL',true,
   'ROUTE_LOCKED','Canonical universe source.');

select zk.audit_procurement_spec_complete('first-actual-dataset-v1','v1');

select domain,route_id,status
from zk.procurement_routes
where specification_id='first-actual-dataset-v1'
order by domain;
