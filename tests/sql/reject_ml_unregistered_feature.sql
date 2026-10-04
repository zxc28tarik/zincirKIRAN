\set ON_ERROR_STOP on
insert into zk.ml_challenger_specs values (
    'reject-unregistered-feature','v1',20,'universe-v1',
    'future_market_relative_total_return',1.0,1,
    timestamptz '2026-01-01 00:00:00+00','CANDIDATE',now()
);
insert into zk.ml_challenger_features values
    ('reject-unregistered-feature','v1','momentum',0,now());
insert into zk.ml_challenger_fits values (
    'fit-reject-unregistered-feature','reject-unregistered-feature','v1',
    'snapshot-v1',timestamptz '2026-06-01 00:00:00+00',
    timestamptz '2026-05-31 00:00:00+00',1,'hash',now()
);
insert into zk.ml_feature_observations (
    fit_id,security_id,observation_at,feature_id,feature_value,available_at
) values (
    'fit-reject-unregistered-feature','AAA',
    timestamptz '2026-02-01 00:00:00+00',
    'value',1.0,
    timestamptz '2026-02-01 00:00:00+00'
);
