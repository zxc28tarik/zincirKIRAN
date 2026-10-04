\set ON_ERROR_STOP on
update zk.portfolio_specs
set target_position_count = 99
where specification_id = 'portfolio-smoke'
  and definition_version = 'v1';
