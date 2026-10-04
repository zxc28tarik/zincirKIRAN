\set ON_ERROR_STOP on
insert into zk.kap_enumeration_runs (
 run_id,captured_at,windows_requested,windows_succeeded,windows_failed,
 distinct_disclosures,correction_edges,status,completeness_guaranteed,blocker_code
) values ('bad-edge',now(),1,1,0,2,1,'ENUMERATED_WITH_CORRECTION_CHAINS',false,'NO_COMPLETENESS');
insert into zk.kap_correction_edges (
 run_id,older_disclosure_id,newer_disclosure_id,older_published_at,
 newer_published_at,relation_label
) values (
 'bad-edge','2','1',
 timestamptz '2023-03-21 15:32:11+00',
 timestamptz '2023-03-09 15:36:13+00',
 'bad'
);
