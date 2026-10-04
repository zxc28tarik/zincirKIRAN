\set ON_ERROR_STOP on
insert into zk.experimental_factor_definitions (
 factor_id,definition_version,economic_family,specification,expected_direction
) values ('immutable','v1','QUALITY','x','HIGHER_IS_BETTER');
update zk.experimental_factor_definitions set specification='changed'
where factor_id='immutable' and definition_version='v1';
