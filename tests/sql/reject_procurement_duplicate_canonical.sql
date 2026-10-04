\set ON_ERROR_STOP on
insert into zk.procurement_specs values ('reject-dup','v1',now()-interval '1 day',false,now());
insert into zk.procurement_routes (
 specification_id,definition_version,domain,route_id,source_id,source_surface,
 access_class,pit_suitability,canonical,status,rationale
) values
 ('reject-dup','v1','PRICES','route-1','borsa_istanbul','one',
  'FREE_PUBLIC','CANONICAL',true,'ROUTE_LOCKED','one'),
 ('reject-dup','v1','PRICES','route-2','borsa_istanbul','two',
  'FREE_PUBLIC','CANONICAL',true,'ROUTE_LOCKED','two');
