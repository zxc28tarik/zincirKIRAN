\set ON_ERROR_STOP on
insert into zk.analyst_estimate_snapshots (
 ticker,fiscal_period_end,estimate_at,authority,eps_consensus,source
) values (
 'Y',timestamptz '2027-12-31 00:00:00+00',timestamptz '2026-08-01 00:00:00+00',
 'CURRENT_ONLY',1,'INVESTINGPRO'
);
update zk.analyst_estimate_snapshots set eps_consensus=2 where ticker='Y';
