\set ON_ERROR_STOP on
insert into zk.experimental_factor_lab_runs (
 run_id,dataset_id,factor_id,factor_definition_version,horizon_days,direction,
 quantile_count,cost_model_id,preregistered_at,executed_at
) values (
 'immutable-run','d','f','v1',20,'HIGHER_IS_BETTER',2,'cost',
 now()-interval '2 minute',now()-interval '1 minute'
);
insert into zk.experimental_factor_lab_periods (
 run_id,as_of,sample_size,total_observations,coverage
) values ('immutable-run',date '2025-01-01',2,2,1.0);
update zk.experimental_factor_lab_periods set coverage=0.5
where run_id='immutable-run' and as_of=date '2025-01-01';
