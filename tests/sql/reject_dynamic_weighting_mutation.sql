\set ON_ERROR_STOP on
update zk.dynamic_weighting_specs
set multiplier_ceiling = 9.0
where specification_id = 'dynamic-smoke'
  and definition_version = 'v1';
