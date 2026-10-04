\set ON_ERROR_STOP on
insert into zk.analyst_estimate_snapshots (
 ticker,fiscal_period_end,estimate_at,authority,eps_consensus,source
) values
 ('X',timestamptz '2027-12-31 00:00:00+00',timestamptz '2026-08-01 00:00:00+00','CURRENT_ONLY',1,'INVESTINGPRO'),
 ('X',timestamptz '2027-12-31 00:00:00+00',timestamptz '2026-09-01 00:00:00+00','HISTORICAL_PIT',2,'INVESTINGPRO');
insert into zk.analyst_estimate_revisions (
 ticker,fiscal_period_end,earlier_at,later_at,eps_revision,source
) values (
 'X',timestamptz '2027-12-31 00:00:00+00',
 timestamptz '2026-08-01 00:00:00+00',timestamptz '2026-09-01 00:00:00+00',1,'INVESTINGPRO'
);
