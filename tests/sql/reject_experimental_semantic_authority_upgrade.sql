\set ON_ERROR_STOP on
insert into zk.experimental_semantic_corpora (
 corpus_id,source_repository,source_commit,authority,total_report_count,total_fact_count,
 own_period_visible_cells,historical_cells
) values (
 'risk','owner/repo',repeat('a',40),'EXPERIMENTAL_VERSION_RISK',1,1,1,1
);
select zk.require_experimental_semantic_authority('risk','AUTHORITATIVE_PIT');
