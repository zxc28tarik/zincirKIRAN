\set ON_ERROR_STOP on
insert into zk.ml_challenger_specs values (
    'reject-future-target','v1',20,'universe-v1',
    'future_market_relative_total_return',1.0,1,
    timestamptz '2026-01-01 00:00:00+00','CANDIDATE',now()
);
insert into zk.ml_challenger_features values
    ('reject-future-target','v1','momentum',0,now());
insert into zk.ml_challenger_fits values (
    'fit-reject-future-target','reject-future-target','v1',
    'snapshot-v1',timestamptz '2026-06-01 00:00:00+00',
    timestamptz '2026-05-31 00:00:00+00',1,'hash',now()
);
insert into zk.ml_training_observations (
    fit_id,security_id,observation_at,target_available_at,target_value
) values (
    'fit-reject-future-target','AAA',
    timestamptz '2026-02-01 00:00:00+00',
    timestamptz '2026-06-02 00:00:00+00',0.02
);
