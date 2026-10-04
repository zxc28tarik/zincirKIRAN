\set ON_ERROR_STOP on
insert into zk.procurement_specs values ('reject-proc','v1',now()-interval '1 day',false,now());
update zk.procurement_specs set definition_version='v2'
where specification_id='reject-proc' and definition_version='v1';
