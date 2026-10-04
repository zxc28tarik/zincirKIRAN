\set ON_ERROR_STOP on
insert into zk.market_bootstrap_artifacts values (
 'x','owner/repo',repeat('a',40),'x.csv',repeat('b',64),
 'VALIDATED_DERIVED_MARKET_DATA',1,null,null,'x',now()
);
update zk.market_bootstrap_artifacts set row_count=2 where artifact_id='x';
