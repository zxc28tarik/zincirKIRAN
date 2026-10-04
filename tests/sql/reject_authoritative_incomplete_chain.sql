\set ON_ERROR_STOP on
insert into zk.financial_version_chains (
 ticker,period_end,enumeration_complete,authority
) values ('AAA',date '2024-12-31',false,'AUTHORITATIVE_PIT');
