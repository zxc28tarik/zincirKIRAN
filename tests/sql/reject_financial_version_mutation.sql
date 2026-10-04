\set ON_ERROR_STOP on
insert into zk.financial_version_chains (
 ticker,period_end,enumeration_complete,authority
) values ('CCC',date '2024-12-31',true,'AUTHORITATIVE_PIT');
insert into zk.financial_versions (
 ticker,period_end,disclosure_id,published_at,raw_sha256,version_sequence,version_tag
) values (
 'CCC',date '2024-12-31','1',now(),repeat('a',64),1,'ORIGINAL'
);
update zk.financial_versions set version_tag='CHANGED'
where ticker='CCC' and period_end=date '2024-12-31' and disclosure_id='1';
