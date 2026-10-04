\set ON_ERROR_STOP on

insert into zk.experimental_factor_definitions (
 factor_id,definition_version,economic_family,specification,expected_direction
) values
 ('gross_profitability','v1','PROFITABILITY','TTM Gross Profit / average assets','HIGHER_IS_BETTER'),
 ('asset_growth','v1','INVESTMENT_DISCIPLINE','Assets_t / Assets_t-4q - 1','LOWER_IS_BETTER'),
 ('momentum_12_1','v1','PRICE_MOMENTUM','Close[t-21] / Close[t-252] - 1','HIGHER_IS_BETTER');

insert into zk.experimental_factor_values (
 dataset_id,factor_id,definition_version,security_id,as_of,value
) values (
 'zk-experimental-factor-lab-v1','gross_profitability','v1','AAA',date '2025-01-02',0.30
);

insert into zk.experimental_factor_values (
 dataset_id,factor_id,definition_version,security_id,as_of,value,unavailable_reason
) values (
 'zk-experimental-factor-lab-v1','momentum_12_1','v1','BBB',date '2025-01-02',null,'INSUFFICIENT_HISTORY'
);

select zk.require_experimental_factor_authority(
 'gross_profitability','v1','EXPERIMENTAL_VERSION_RISK'
);
