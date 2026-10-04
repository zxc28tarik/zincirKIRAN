\set ON_ERROR_STOP on

insert into zk.experimental_factor_datasets (
 dataset_id,authority,historical_cells,cells_with_visible_financial_facts
) values (
 'zk-experimental-factor-lab-v1','EXPERIMENTAL_VERSION_RISK',6000,5633
);

insert into zk.experimental_factor_dataset_inputs (
 dataset_id,artifact_id,sha256,authority,scope_note
) values
 ('zk-experimental-factor-lab-v1','market',
  'b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141',
  'VALIDATED_DERIVED_MARKET_DATA','Historical member market data.'),
 ('zk-experimental-factor-lab-v1','semantic',
  '07863ddbd78924ad276e7d0aeba7fa6eec9733477b4ca3c02ece285bcf1d9e7a',
  'EXPERIMENTAL_VERSION_RISK','Semantic financial facts.');

insert into zk.experimental_forward_label_specs values
 ('zk-experimental-factor-lab-v1',20,'future_market_relative_return',
  'EXACT_TRADING_DAY_INDEX','UNAVAILABLE_NOT_ZERO',now()),
 ('zk-experimental-factor-lab-v1',60,'future_market_relative_return',
  'EXACT_TRADING_DAY_INDEX','UNAVAILABLE_NOT_ZERO',now()),
 ('zk-experimental-factor-lab-v1',120,'future_market_relative_return',
  'EXACT_TRADING_DAY_INDEX','UNAVAILABLE_NOT_ZERO',now()),
 ('zk-experimental-factor-lab-v1',252,'future_market_relative_return',
  'EXACT_TRADING_DAY_INDEX','UNAVAILABLE_NOT_ZERO',now());

select zk.require_experimental_factor_dataset(
 'zk-experimental-factor-lab-v1','EXPERIMENTAL_VERSION_RISK'
);
