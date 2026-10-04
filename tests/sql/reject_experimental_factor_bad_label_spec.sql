\set ON_ERROR_STOP on
insert into zk.experimental_factor_datasets (
 dataset_id,authority,historical_cells,cells_with_visible_financial_facts
) values ('bad-label','EXPERIMENTAL_VERSION_RISK',1,1);
insert into zk.experimental_forward_label_specs (
 dataset_id,horizon_days,target,calendar_basis,missing_policy
) values (
 'bad-label',20,'future_market_relative_return','CALENDAR_DAYS','UNAVAILABLE_NOT_ZERO'
);
