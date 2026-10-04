\set ON_ERROR_STOP on
insert into zk.experimental_factor_datasets (
 dataset_id,authority,historical_cells,cells_with_visible_financial_facts,production_eligible
) values ('bad-prod','EXPERIMENTAL_VERSION_RISK',1,1,true);
