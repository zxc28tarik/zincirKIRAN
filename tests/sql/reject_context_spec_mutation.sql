\set ON_ERROR_STOP on
update zk.context_research_specs
set success_criteria = 'changed after results'
where specification_id = 'context-smoke'
  and definition_version = 'v1';
