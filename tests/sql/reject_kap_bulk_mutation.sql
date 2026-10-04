\set ON_ERROR_STOP on
insert into zk.kap_bulk_financial_archives values (
 2020,'3A',1,'x.zip','https://kap.org.tr/tr/api/financialTable/download/2020/1',
 repeat('a',64),1,1,true,'RAW_EVIDENCE',now()
);
update zk.kap_bulk_financial_archives set member_count=2 where year=2020 and period_code=1;
