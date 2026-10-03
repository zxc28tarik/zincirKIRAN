\set ON_ERROR_STOP on
insert into zk.factor_registry (factor_id, definition_version, economic_family, economic_concept_key, specification, required_fields)
values
 ('alpha_dup_comp_a','v1','VALUE','alpha_dup_comp','a','["x"]'::jsonb),
 ('alpha_dup_comp_b','v1','VALUE','alpha_dup_comp','b','["x"]'::jsonb);
insert into zk.factor_experiments (experiment_id,factor_id,factor_definition_version,horizon_days,data_snapshot_id,universe_rule_version,quantile_count,cost_model_id,hypothesis,expected_direction,preregistered_at)
values
 ('alpha-dup-exp-a','alpha_dup_comp_a','v1',20,'snap','uni',5,'cost','a','UNDECIDED',now()),
 ('alpha-dup-exp-b','alpha_dup_comp_b','v1',20,'snap','uni',5,'cost','b','UNDECIDED',now());
insert into zk.decorrelation_runs (run_id,data_snapshot_id,universe_rule_version,correlation_method,minimum_overlap,absolute_threshold,residualization_include_intercept,preregistered_at)
values ('alpha-dup-decor','snap','uni','SPEARMAN',20,0.8,true,now());
insert into zk.decorrelation_components (run_id,component_no,factor_id,definition_version)
values
 ('alpha-dup-decor',1,'alpha_dup_comp_a','v1'),
 ('alpha-dup-decor',1,'alpha_dup_comp_b','v1');
insert into zk.alpha_aggregation_specs (specification_id,definition_version,horizon_days,aggregation_rule_id,normalization_rule_id,weight_policy_id,coverage_rule_id,parameters)
values ('alpha-dup-spec','v1',20,'WEIGHTED_SUM','NORM','WEIGHTS','ABS_WEIGHT_COVERAGE','{"minimum_coverage":"0.5"}'::jsonb);
insert into zk.alpha_factor_admissions (admission_id,factor_id,factor_definition_version,horizon_days,decision,factor_lab_experiment_id,decorrelation_run_id,decorrelation_component_no,rationale)
values
 ('alpha-dup-adm-a','alpha_dup_comp_a','v1',20,'ADMITTED','alpha-dup-exp-a','alpha-dup-decor',1,'a'),
 ('alpha-dup-adm-b','alpha_dup_comp_b','v1',20,'ADMITTED','alpha-dup-exp-b','alpha-dup-decor',1,'b');
insert into zk.alpha_factor_weights (specification_id,definition_version,admission_id,weight)
values ('alpha-dup-spec','v1','alpha-dup-adm-a',1.0);
insert into zk.alpha_factor_weights (specification_id,definition_version,admission_id,weight)
values ('alpha-dup-spec','v1','alpha-dup-adm-b',1.0);
