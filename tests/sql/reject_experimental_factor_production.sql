\set ON_ERROR_STOP on
insert into zk.experimental_factor_definitions (
 factor_id,definition_version,economic_family,specification,expected_direction,
 production_eligible
) values ('prod','v1','QUALITY','x','HIGHER_IS_BETTER',true);
