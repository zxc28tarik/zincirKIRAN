\set ON_ERROR_STOP on
insert into zk.investingpro_export_batches (
 batch_id,exported_at,filter_description,row_count,content_sha256,authority
) values (
 'immutable-batch',now(),'BIST',1,repeat('b',64),'CURRENT_SCREENER_SNAPSHOT'
);
update zk.investingpro_export_batches set row_count=2 where batch_id='immutable-batch';
