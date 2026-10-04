\set ON_ERROR_STOP on
insert into zk.current_bootstrap_artifacts values (
 'hist','owner/repo',repeat('a',40),'x',repeat('b',64),
 'CURRENT_MARKET_SNAPSHOT',1,'x',now()
);
select zk.reject_current_artifact_for_historical_use('hist');
