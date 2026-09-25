\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, required_fields
) values (
    'missing_inputs_factor', 'v1', 'RISK', 'missing_inputs',
    'test', '[]'::jsonb
);
