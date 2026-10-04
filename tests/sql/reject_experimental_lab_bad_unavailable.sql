\set ON_ERROR_STOP on
insert into zk.experimental_factor_lab_runs (
 run_id,dataset_id,factor_id,factor_definition_version,horizon_days,direction,
 quantile_count,cost_model_id,preregistered_at,executed_at
) values (
 'bad-unavailable','d','f','v1',20,'HIGHER_IS_BETTER',2,'cost',
 now()-interval '2 minute',now()-interval '1 minute'
);
insert into zk.experimental_factor_lab_periods (
 run_id,as_of,sample_size,total_observations,coverage,unavailable_reason
) values ('bad-unavailable',date '2025-01-01',null,null,null,null);
