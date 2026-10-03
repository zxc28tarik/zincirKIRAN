\set ON_ERROR_STOP on
insert into zk.companies (company_id,legal_name) values ('73000000-0000-0000-0000-000000000001'::uuid,'Alpha Incomplete Co');
insert into zk.securities (security_id,company_id) values ('73000000-0000-0000-0000-000000000002'::uuid,'73000000-0000-0000-0000-000000000001'::uuid);
insert into zk.factor_registry (factor_id,definition_version,economic_family,economic_concept_key,specification,required_fields)
values ('alpha_incomplete_factor','v1','VALUE','alpha_incomplete_factor','x','["x"]'::jsonb);
insert into zk.factor_experiments (experiment_id,factor_id,factor_definition_version,horizon_days,data_snapshot_id,universe_rule_version,quantile_count,cost_model_id,hypothesis,expected_direction,preregistered_at)
values ('alpha-incomplete-exp','alpha_incomplete_factor','v1',20,'snap','uni',5,'cost','x','UNDECIDED',now());
insert into zk.decorrelation_runs (run_id,data_snapshot_id,universe_rule_version,correlation_method,minimum_overlap,absolute_threshold,residualization_include_intercept,preregistered_at)
values ('alpha-incomplete-decor','snap','uni','PEARSON',20,0.8,true,now());
insert into zk.decorrelation_components (run_id,component_no,factor_id,definition_version)
values ('alpha-incomplete-decor',1,'alpha_incomplete_factor','v1');
insert into zk.alpha_aggregation_specs (specification_id,definition_version,horizon_days,aggregation_rule_id,normalization_rule_id,weight_policy_id,coverage_rule_id,parameters)
values ('alpha-incomplete-spec','v1',20,'WEIGHTED_SUM','NORM','WEIGHTS','ABS_WEIGHT_COVERAGE','{"minimum_coverage":"0.5"}'::jsonb);
insert into zk.alpha_factor_admissions (admission_id,factor_id,factor_definition_version,horizon_days,decision,factor_lab_experiment_id,decorrelation_run_id,decorrelation_component_no,rationale)
values ('alpha-incomplete-adm','alpha_incomplete_factor','v1',20,'ADMITTED','alpha-incomplete-exp','alpha-incomplete-decor',1,'x');
insert into zk.alpha_factor_weights (specification_id,definition_version,admission_id,weight)
values ('alpha-incomplete-spec','v1','alpha-incomplete-adm',1.0);
begin;
insert into zk.alpha_runs (alpha_run_id,specification_id,definition_version,security_id,evaluated_at,alpha_field,status,alpha_value,coverage,planned_factor_count,available_factor_count,planned_absolute_weight,available_absolute_weight)
values ('alpha-incomplete-run','alpha-incomplete-spec','v1','73000000-0000-0000-0000-000000000002'::uuid,now(),'Alpha20','SCORED',0.5,1.0,1,1,1.0,1.0);
commit;
