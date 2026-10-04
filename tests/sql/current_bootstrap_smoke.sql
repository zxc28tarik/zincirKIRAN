\set ON_ERROR_STOP on
insert into zk.current_bootstrap_artifacts values (
 'current-kap-bist-roster','zxc28tarik/TOTAL-RASYO-HESAPLAYICI',
 'd0c5ce25832dc94c138fc6141bba8fa8392cd00b',
 'data/live/current_total_rasyo_v1/universe.csv',
 'd9c860f918a538bc6426bd45e5e91ae4eb60fef188fda3630eef7fa78b83e4a1',
 'CURRENT_ROSTER_DISCOVERY_ONLY',807,'Current KAP roster.',now()
);
select artifact_id,row_count from zk.current_bootstrap_artifacts;
