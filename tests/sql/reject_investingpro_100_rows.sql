\set ON_ERROR_STOP on
insert into zk.investingpro_export_batches (
 batch_id,exported_at,filter_description,row_count,content_sha256,authority
) values (
 'too-large',now(),'BIST',100,repeat('a',64),'CURRENT_SCREENER_SNAPSHOT'
);
