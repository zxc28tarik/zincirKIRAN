\set ON_ERROR_STOP on
insert into zk.corporate_action_evidence (
 event_id,published_at,ticker,subject,event_type,authority,source_sha256,source_system
) values (
 'x',now(),'AAA','Birleşme','MERGER',
 'POSITIVE_EVENT_EVIDENCE',repeat('a',64),'KAP'
);
update zk.corporate_action_evidence set subject='changed' where event_id='x';
