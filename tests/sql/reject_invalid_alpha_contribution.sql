\set ON_ERROR_STOP on
insert into zk.companies (company_id,legal_name) values ('72000000-0000-0000-0000-000000000001'::uuid,'Alpha Bad Contribution Co');
insert into zk.securities (security_id,company_id) values ('72000000-0000-0000-0000-000000000002'::uuid,'72000000-0000-0000-0000-000000000001'::uuid);
insert into zk.factor_registry (factor_id,definition_version,economic_family,economic_concept_key,specification,required_fields)
values ('alpha_bad_contrib_factor','v1','QUALITY','alpha_bad_contrib_factor','x','["x"]'::jsonb);
insert into zk.factor_experiments (experiment_id,factor_id,factor_definition_version,horizon_days,data_snapshot_id,universe_rule_version,quantile_count,cost_model_id,hypothesis,expected_direction,preregistered_at)
values ('alpha-bad-contrib-exp','alpha_bad_contrib_factor','v1',20,'snap','uni',5,'cost','x','UNDECIDED',now());
insert into zk.decorrelation_runs (run_id,data_snapshot_id,universe_rule_version,correlation_method,minimum_overlap,absolute_threshold,residualization_include_intercept,preregistered_at)
values ('alpha-bad-contrib-decor','snap','uni','PEARSON',20,0.8,true,now());
insert into zk.decorrelation_components (run_id,component_no,factor_id,definition_version)
values ('alpha-bad-contrib-decor',1,'alpha_bad_contrib_factor','v1');
insert into zk.alpha_aggregation_specs (specification_id,definition_version,horizon_days,aggregation_rule_id,normalization_rule_id,weight_policy_id,coverage_rule_id,parameters)
values ('alpha-bad-contrib-spec','v1',20,'WEIGHTED_SUM','NORM_A','WEIGHTS','ABS_WEIGHT_COVERAGE','{"minimum_coverage":"0.5"}'::jsonb);
insert into zk.alpha_factor_admissions (admission_id,factor_id,factor_definition_version,horizon_days,decision,factor_lab_experiment_id,decorrelation_run_id,decorrelation_component_no,rationale)
values ('alpha-bad-contrib-adm','alpha_bad_contrib_factor','v1',20,'ADMITTED','alpha-bad-contrib-exp','alpha-bad-contrib-decor',1,'x');
insert into zk.alpha_factor_weights (specification_id,definition_version,admission_id,weight)
values ('alpha-bad-contrib-spec','v1','alpha-bad-contrib-adm',2.0);
begin;
insert into zk.alpha_runs (alpha_run_id,specification_id,definition_version,security_id,evaluated_at,alpha_field,status,alpha_value,coverage,planned_factor_count,available_factor_count,planned_absolute_weight,available_absolute_weight)
values ('alpha-bad-contrib-run','alpha-bad-contrib-spec','v1','72000000-0000-0000-0000-000000000002'::uuid,now(),'Alpha20','SCORED',0.5,1.0,1,1,2.0,2.0);
insert into zk.alpha_run_contributions (alpha_run_id,admission_id,raw_signal_value,normalization_rule_id,normalized_value,weight,weighted_contribution)
values ('alpha-bad-contrib-run','alpha-bad-contrib-adm',0.2,'WRONG_NORM','APPLIES','COMPARABLE',0.25,2.0,0.5);
commit;
