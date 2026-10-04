\set ON_ERROR_STOP on

insert into zk.experimental_semantic_corpora (
 corpus_id,source_repository,source_commit,authority,
 total_report_count,total_fact_count,own_period_visible_cells,historical_cells
) values (
 'total-rasyo-experimental-semantic-facts-v1',
 'zxc28tarik/TOTAL-RASYO-HESAPLAYICI',
 'c8b481e79e270f2c095e8c180671a3f483f0775e',
 'EXPERIMENTAL_VERSION_RISK',
 5052,199969,5633,6000
);

insert into zk.experimental_semantic_artifacts (
 corpus_id,artifact_id,source_path,sha256,report_count,fact_count,authority,scope_note
) values (
 'total-rasyo-experimental-semantic-facts-v1',
 'semantic-primary',
 'data/backtest_sources/experimental_semantic_facts_v1/semantic_reports.jsonl.gz',
 '07863ddbd78924ad276e7d0aeba7fa6eec9733477b4ca3c02ece285bcf1d9e7a',
 4581,195782,'EXPERIMENTAL_VERSION_RISK','Primary semantic facts.'
);

insert into zk.experimental_semantic_risks values
 ('total-rasyo-experimental-semantic-facts-v1','ORIGINAL_CATALOG_BYTES_UNAVAILABLE',now()),
 ('total-rasyo-experimental-semantic-facts-v1','SUPERSEDED_HISTORICAL_KAP_REPORT_VERSIONS_NOT_ENUMERATED',now());

select zk.require_experimental_semantic_authority(
 'total-rasyo-experimental-semantic-facts-v1',
 'EXPERIMENTAL_VERSION_RISK'
);
