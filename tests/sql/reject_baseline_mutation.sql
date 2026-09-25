\set ON_ERROR_STOP on

insert into zk.baseline_definitions (
    baseline_id, definition_version, formula, baseline_role
) values (
    'SIMPLE_VALUE', 'immutable-v1', 'formula-a', 'COMPARATOR'
);

update zk.baseline_definitions
set formula = 'formula-changed-after-results'
where baseline_id = 'SIMPLE_VALUE'
  and definition_version = 'immutable-v1';
