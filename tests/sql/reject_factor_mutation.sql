\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values (
    'immutable_factor', 'v1', 'QUALITY', 'immutable_test',
    'formula-a', '["x"]'::jsonb
);

update zk.factor_registry
set specification = 'changed-after-results'
where factor_id = 'immutable_factor' and definition_version = 'v1';
