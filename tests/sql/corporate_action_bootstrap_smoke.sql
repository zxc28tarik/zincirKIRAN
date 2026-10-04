\set ON_ERROR_STOP on

insert into zk.corporate_action_evidence (
 event_id,published_at,ticker,subject,event_type,authority,source_sha256,source_system
) values (
 '123', timestamptz '2023-01-01 10:00:00+00','AAA','Sermaye Artırımı',
 'CAPITAL_INCREASE','POSITIVE_EVENT_EVIDENCE',repeat('a',64),'KAP'
);

insert into zk.corporate_action_covered_windows (
 window_id,start_at,end_at,complete,source_manifest_sha256
) values (
 '2016-05_2026-07',
 timestamptz '2016-05-01 00:00:00+00',
 timestamptz '2026-07-31 23:59:59+00',
 true,
 '1935232295360b1026a036e725809e0e73a62253ce07145bbc1f13fd6abd1345'
);

select event_type,authority from zk.corporate_action_evidence;
