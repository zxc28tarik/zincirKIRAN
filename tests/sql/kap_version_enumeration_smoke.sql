\set ON_ERROR_STOP on
insert into zk.kap_enumeration_runs (
 run_id,captured_at,windows_requested,windows_succeeded,windows_failed,
 distinct_disclosures,correction_edges,status,completeness_guaranteed,blocker_code
) values (
 'enum-smoke',now(),60,1,59,423,1,'ENUMERATED_PARTIAL',false,
 'COMPLETENESS_GUARANTEE_ABSENT'
);

insert into zk.kap_enumeration_windows (
 run_id,window_id,start_at,end_at,http_status,request_sha256,response_sha256,
 result_count,status
) values (
 'enum-smoke','2023-03',
 timestamptz '2023-03-01 00:00:00+00',
 timestamptz '2023-04-01 00:00:00+00',
 200,repeat('a',64),
 '29bb3d7bd3bef0e07c4a1855416751b85ba61affc2d04e973873a16a59f69305',
 423,'SUCCESS'
);

insert into zk.kap_correction_edges (
 run_id,older_disclosure_id,newer_disclosure_id,older_published_at,
 newer_published_at,relation_label
) values (
 'enum-smoke','1122417','1126845',
 timestamptz '2023-03-09 15:36:13+00',
 timestamptz '2023-03-21 15:32:11+00',
 'Düzeltilmiş Bildirim'
);

select run_id,status,completeness_guaranteed
from zk.kap_enumeration_runs;
