\set ON_ERROR_STOP on
insert into zk.experimental_factor_definitions (
 factor_id,definition_version,economic_family,specification,expected_direction
) values ('missing','v1','QUALITY','x','HIGHER_IS_BETTER');
insert into zk.experimental_factor_values (
 dataset_id,factor_id,definition_version,security_id,as_of,value,unavailable_reason
) values ('d','missing','v1','AAA',date '2025-01-01',null,null);
