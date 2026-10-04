\set ON_ERROR_STOP on
insert into zk.kap_enumeration_runs (
 run_id,captured_at,windows_requested,windows_succeeded,windows_failed,
 distinct_disclosures,correction_edges,status,completeness_guaranteed,blocker_code
) values ('bad-complete',now(),60,60,0,1000,10,'ENUMERATED_WITH_CORRECTION_CHAINS',true,'NONE');
