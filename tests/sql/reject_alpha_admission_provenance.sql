\set ON_ERROR_STOP on
insert into zk.factor_registry (factor_id, definition_version, economic_family, economic_concept_key, specification, required_fields)
values
 ('alpha_bad_prov_a','v1','VALUE','alpha_bad_prov_a','a','["x"]'::jsonb),
 ('alpha_bad_prov_b','v1','VALUE','alpha_bad_prov_b','b','["x"]'::jsonb);
insert into zk.factor_experiments (experiment_id,factor_id,factor_definition_version,horizon_days,data_snapshot_id,universe_rule_version,quantile_count,cost_model_id,hypothesis,expected_direction,preregistered_at)
values ('alpha-bad-prov-exp','alpha_bad_prov_b','v1',20,'snap','uni',5,'cost','bad','UNDECIDED',now());
insert into zk.decorrelation_runs (run_id,data_snapshot_id,universe_rule_version,correlation_method,minimum_overlap,absolute_threshold,residualization_include_intercept,preregistered_at)
values ('alpha-bad-prov-decor','snap','uni','PEARSON',20,0.8,true,now());
insert into zk.decorrelation_components (run_id,component_no,factor_id,definition_version)
values ('alpha-bad-prov-decor',1,'alpha_bad_prov_a','v1');
insert into zk.alpha_factor_admissions (admission_id,factor_id,factor_definition_version,horizon_days,decision,factor_lab_experiment_id,decorrelation_run_id,decorrelation_component_no,rationale)
values ('alpha-bad-prov-adm','alpha_bad_prov_a','v1',20,'ADMITTED','alpha-bad-prov-exp','alpha-bad-prov-decor',1,'bad provenance');
