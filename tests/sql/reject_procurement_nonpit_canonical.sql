\set ON_ERROR_STOP on
insert into zk.procurement_specs values ('reject-nonpit','v1',now()-interval '1 day',false,now());
insert into zk.procurement_routes (
 specification_id,definition_version,domain,route_id,source_id,source_surface,
 access_class,pit_suitability,canonical,status,rationale
) values (
 'reject-nonpit','v1','PRICES','bad-route','vendor','latest adjusted close',
 'OWNER_ACCESS_ENRICHMENT','CONDITIONAL',true,'ROUTE_LOCKED','bad'
);
