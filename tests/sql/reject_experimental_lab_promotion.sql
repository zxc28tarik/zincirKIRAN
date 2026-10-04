\set ON_ERROR_STOP on
insert into zk.experimental_factor_lab_runs (
 run_id,dataset_id,factor_id,factor_definition_version,horizon_days,direction,
 quantile_count,cost_model_id,preregistered_at,executed_at
) values (
 'promote','d','f','v1',20,'HIGHER_IS_BETTER',2,'cost',
 now()-interval '2 minute',now()-interval '1 minute'
);
select zk.reject_experimental_lab_promotion('promote');
