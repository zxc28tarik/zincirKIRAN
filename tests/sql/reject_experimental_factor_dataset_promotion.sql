\set ON_ERROR_STOP on
insert into zk.experimental_factor_datasets (
 dataset_id,authority,historical_cells,cells_with_visible_financial_facts
) values ('risk','EXPERIMENTAL_VERSION_RISK',1,1);
select zk.require_experimental_factor_dataset('risk','AUTHORITATIVE_PIT');
