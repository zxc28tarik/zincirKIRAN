\set ON_ERROR_STOP on
insert into zk.market_bootstrap_artifacts values (
 'derived','owner/repo',repeat('a',40),'x.csv',repeat('b',64),
 'VALIDATED_DERIVED_MARKET_DATA',1,null,null,'derived',now()
);
select zk.require_official_borsa_market_artifact('derived');
