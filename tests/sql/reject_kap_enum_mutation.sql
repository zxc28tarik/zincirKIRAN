\set ON_ERROR_STOP on
insert into zk.kap_enumeration_runs (
 run_id,captured_at,windows_requested,windows_succeeded,windows_failed,
 distinct_disclosures,correction_edges,status,completeness_guaranteed,blocker_code
) values ('bad-mutation',now(),0,0,0,0,0,'ENUMERATION_NOT_RUN',false,'NOT_RUN');
update zk.kap_enumeration_runs set blocker_code='changed' where run_id='bad-mutation';
