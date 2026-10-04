\set ON_ERROR_STOP on
insert into zk.investingpro_export_batches (
 batch_id,exported_at,filter_description,row_count,content_sha256,authority
) values (
 'current-batch',now(),'BIST',1,repeat('a',64),'CURRENT_ESTIMATE_SNAPSHOT'
);
insert into zk.investingpro_estimate_observations (
 ticker,metric,period_label,observed_at,value,source_batch_id,authority
) values (
 'AAA','EPS_ESTIMATE','FY2027',timestamptz '2026-10-04 20:00:00+00',1.0,
 'current-batch','CURRENT_ESTIMATE_SNAPSHOT'
);
select zk.require_timestamped_investingpro_history(
 'AAA','EPS_ESTIMATE','FY2027',timestamptz '2026-10-04 20:00:00+00','current-batch'
);
