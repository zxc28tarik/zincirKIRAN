\set ON_ERROR_STOP on
insert into zk.current_bootstrap_artifacts values (
 'x','owner/repo',repeat('a',40),'x',repeat('b',64),
 'CURRENT_MARKET_SNAPSHOT',1,'x',now()
);
update zk.current_bootstrap_artifacts set row_count=2 where artifact_id='x';
