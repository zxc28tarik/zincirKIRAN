\set ON_ERROR_STOP on
insert into zk.official_source_definitions values (
 'reject-block-source','Source','https://example.invalid',true,'note',true,now()
);
insert into zk.acquisition_attempts (
 acquisition_id,source_id,requested_url,attempted_at,status
) values (
 'reject-block','reject-block-source','https://example.invalid',now(),'BLOCKED'
);
