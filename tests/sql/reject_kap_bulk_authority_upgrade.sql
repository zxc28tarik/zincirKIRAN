\set ON_ERROR_STOP on
insert into zk.kap_bulk_financial_archives (
 year,period,period_code,filename,download_url,sha256,member_count,size_bytes,
 exact_manifest_match,authority
) values (
 2022,'3A',1,'x.zip','https://kap.org.tr/tr/api/financialTable/download/2022/1',
 repeat('a',64),1,1,true,'CANONICAL_PIT'
);
