\set ON_ERROR_STOP on

insert into zk.experimental_factor_lab_runs (
 run_id,dataset_id,factor_id,factor_definition_version,horizon_days,direction,
 quantile_count,cost_model_id,preregistered_at,executed_at
) values (
 'lab-smoke','zk-experimental-factor-lab-v1','gross_profitability','v1',20,
 'HIGHER_IS_BETTER',5,'research-zero-cost',
 timestamptz '2026-10-04 20:00:00+00',
 timestamptz '2026-10-04 20:01:00+00'
);

insert into zk.experimental_factor_lab_periods (
 run_id,as_of,sample_size,total_observations,coverage,ic,monotonicity,
 top_vs_market,bottom_vs_market,top_minus_bottom
) values (
 'lab-smoke',date '2025-01-02',80,100,0.8,0.04,0.9,0.02,-0.01,0.03
);

insert into zk.experimental_factor_lab_summaries (
 run_id,valid_periods,total_periods,mean_ic,icir,mean_coverage,
 mean_top_vs_market,mean_top_minus_bottom
) values (
 'lab-smoke',1,1,0.04,null,0.8,0.02,0.03
);

select run_id,mean_ic,mean_coverage from zk.experimental_factor_lab_summaries;
