\set ON_ERROR_STOP on
insert into zk.experimental_factor_datasets (
 dataset_id,authority,historical_cells,cells_with_visible_financial_facts
) values ('immutable','EXPERIMENTAL_VERSION_RISK',1,1);
update zk.experimental_factor_datasets set historical_cells=2 where dataset_id='immutable';
