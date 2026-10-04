\set ON_ERROR_STOP on
insert into zk.ml_challenger_specs values (
    'reject-prediction-before-fit','v1',20,'universe-v1',
    'future_market_relative_total_return',1.0,1,
    timestamptz '2026-01-01 00:00:00+00','CANDIDATE',now()
);
insert into zk.ml_challenger_features values
    ('reject-prediction-before-fit','v1','momentum',0,now());
insert into zk.ml_challenger_fits values (
    'fit-reject-prediction-before-fit','reject-prediction-before-fit','v1',
    'snapshot-v1',timestamptz '2026-06-01 00:00:00+00',
    timestamptz '2026-05-31 00:00:00+00',1,'hash',now()
);
insert into zk.ml_predictions (
    fit_id,security_id,prediction_at,raw_score
) values (
    'fit-reject-prediction-before-fit','AAA',
    timestamptz '2026-06-01 00:00:00+00',0.1
);
