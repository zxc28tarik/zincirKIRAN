\set ON_ERROR_STOP on
insert into zk.official_source_definitions values (
 'reject-receipt-source','Source','https://example.invalid',true,'note',true,now()
);
insert into zk.acquisition_attempts (
 acquisition_id,source_id,requested_url,attempted_at,status,blocker_code,blocker_detail
) values (
 'reject-receipt','reject-receipt-source','https://example.invalid',now(),'BLOCKED','X','blocked'
);
insert into zk.acquired_artifact_receipts (
 acquisition_id,source_id,source_url,retrieved_at,content_sha256,byte_size
) values (
 'reject-receipt','reject-receipt-source','https://example.invalid',now(),repeat('b',64),1
);
