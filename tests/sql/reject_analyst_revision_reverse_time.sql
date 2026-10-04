\set ON_ERROR_STOP on
insert into zk.analyst_estimate_revisions (
 ticker,fiscal_period_end,earlier_at,later_at,eps_revision,source
) values (
 'X',timestamptz '2027-12-31 00:00:00+00',
 timestamptz '2026-09-01 00:00:00+00',timestamptz '2026-08-01 00:00:00+00',1,'INVESTINGPRO'
);
