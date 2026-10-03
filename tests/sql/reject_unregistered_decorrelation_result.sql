\set ON_ERROR_STOP on

insert into zk.decorrelation_components (
    run_id, component_no, factor_id, definition_version
) values (
    'missing-run', 1, 'missing-factor', 'v1'
);
