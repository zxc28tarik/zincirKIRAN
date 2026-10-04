\set ON_ERROR_STOP on

insert into zk.financial_version_chains (
  ticker,period_end,enumeration_complete,authority
) values (
  'KORTS',date '2022-12-31',true,'AUTHORITATIVE_PIT'
);

insert into zk.financial_versions (
 ticker,period_end,disclosure_id,published_at,raw_sha256,
 version_sequence,version_tag,supersedes_disclosure_id
) values
(
 'KORTS',date '2022-12-31','1122417',
 timestamptz '2023-03-09 18:36:13+03',
 repeat('1',64),1,'ORIGINAL',null
),
(
 'KORTS',date '2022-12-31','1126845',
 timestamptz '2023-03-21 18:32:11+03',
 repeat('2',64),2,'CORRECTION','1122417'
);

select zk.select_financial_version_at_cutoff(
 'KORTS', date '2022-12-31', timestamptz '2023-03-15 12:00:00+00'
);
select zk.select_financial_version_at_cutoff(
 'KORTS', date '2022-12-31', timestamptz '2023-03-22 12:00:00+00'
);
