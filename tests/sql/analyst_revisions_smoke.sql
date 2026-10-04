\set ON_ERROR_STOP on
insert into zk.analyst_estimate_snapshots (
 ticker,fiscal_period_end,estimate_at,authority,eps_consensus,revenue_consensus,
 analyst_count,source
) values
 ('THYAO',timestamptz '2027-12-31 00:00:00+00',timestamptz '2026-08-01 00:00:00+00',
  'HISTORICAL_PIT',10,100,12,'INVESTINGPRO'),
 ('THYAO',timestamptz '2027-12-31 00:00:00+00',timestamptz '2026-09-01 00:00:00+00',
  'HISTORICAL_PIT',11.5,105,13,'INVESTINGPRO');

insert into zk.analyst_estimate_revisions (
 ticker,fiscal_period_end,earlier_at,later_at,eps_revision,revenue_revision,source
) values (
 'THYAO',timestamptz '2027-12-31 00:00:00+00',
 timestamptz '2026-08-01 00:00:00+00',timestamptz '2026-09-01 00:00:00+00',
 1.5,5,'INVESTINGPRO'
);

select ticker,eps_revision,revenue_revision
from zk.analyst_estimate_revisions;
