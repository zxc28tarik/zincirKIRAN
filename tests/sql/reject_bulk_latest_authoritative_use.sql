\set ON_ERROR_STOP on
insert into zk.financial_version_chains (
 ticker,period_end,enumeration_complete,authority
) values ('BBB',date '2024-12-31',false,'BULK_LATEST_ONLY');
select zk.require_authoritative_financial_chain('BBB',date '2024-12-31');
