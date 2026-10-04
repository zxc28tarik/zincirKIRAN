\set ON_ERROR_STOP on
insert into zk.official_source_definitions values (
 'reject-source','Source','https://example.invalid',true,'note',true,now()
);
update zk.official_source_definitions set name='Changed' where source_id='reject-source';
