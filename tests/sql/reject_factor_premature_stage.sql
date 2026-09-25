\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, expected_direction, required_fields, stage
) values (
    'premature_factor', 'v1', 'VALUE', 'premature',
    'not validated', 'UNDECIDED', '["x"]'::jsonb, 'PRODUCTION'
);
