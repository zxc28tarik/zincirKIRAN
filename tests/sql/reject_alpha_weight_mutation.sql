\set ON_ERROR_STOP on
update zk.alpha_factor_weights
set weight = 9.0
where specification_id = 'alpha-engine-smoke'
  and definition_version = 'v1'
  and admission_id = 'alpha-smoke-adm-value';
