\set ON_ERROR_STOP on

insert into zk.kap_bulk_financial_archives (
 year,period,period_code,filename,download_url,sha256,member_count,size_bytes,exact_manifest_match
) values (
 2021,'3A',1,'KAP_2021_3A.zip',
 'https://kap.org.tr/tr/api/financialTable/download/2021/1',
 'd953adceb72accfc4294cce4b40e79121ba10529ad2a17ef3f60e61654ecd654',
 466,16573084,true
);

select year,period,member_count,authority
from zk.kap_bulk_financial_archives;
