\set ON_ERROR_STOP on
insert into zk.experimental_factor_definitions (
 factor_id,definition_version,economic_family,specification,expected_direction
) values ('f','v1','QUALITY','x','HIGHER_IS_BETTER');
select zk.require_experimental_factor_authority('f','v1','AUTHORITATIVE_PIT');
