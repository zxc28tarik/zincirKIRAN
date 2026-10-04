\set ON_ERROR_STOP on

insert into zk.investingpro_export_batches (
 batch_id,exported_at,filter_description,row_count,content_sha256,authority
) values (
 'batch-1',now(),'Turkey | Borsa Istanbul | Primary Trading Item',98,repeat('a',64),
 'CURRENT_ESTIMATE_SNAPSHOT'
);

insert into zk.investingpro_estimate_observations (
 ticker,metric,period_label,observed_at,value,source_batch_id,authority
) values (
 'THYAO','EPS_ESTIMATE','FY2027',now(),10.0,'batch-1','CURRENT_ESTIMATE_SNAPSHOT'
);

select batch_id,row_count,authority from zk.investingpro_export_batches;
