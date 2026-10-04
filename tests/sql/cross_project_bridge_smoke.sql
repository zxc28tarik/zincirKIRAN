\set ON_ERROR_STOP on

insert into zk.cross_project_manifests (
  manifest_id,source_project
) values ('total-rasyo-bootstrap-v1','TOTAL-RASYO-HESAPLAYICI');

insert into zk.cross_project_artifacts (
  manifest_id,source_repository,source_commit,source_path,source_pr,
  evidence_domain,expected_sha256,authority,coverage_note
) values
(
 'total-rasyo-bootstrap-v1','zxc28tarik/TOTAL-RASYO-HESAPLAYICI',
 '445e9a7cb788124a52fd4ac171f3e16e6c67137e',
 'data/backtest_sources/m3_source_package/index_closes.csv.gz',15,
 'PRICES','32a740f7a7114e03c885d1ae75c8bacd081b5254b043521fd76ca5f8e34e786e',
 'CANONICAL_PIT','Benchmark/sector index closes only.'
),
(
 'total-rasyo-bootstrap-v1','zxc28tarik/TOTAL-RASYO-HESAPLAYICI',
 '9a9d6e71677104c10a41e22b5a07547a1e5545d0',
 'data/backtest_sources/kap_bulk_financial_source_capture/public_byte_evidence/acquisition_receipt.run_33568804543.json',38,
 'FINANCIALS',null,'RAW_EVIDENCE_ONLY','Real KAP archives; PIT completeness unresolved.'
);

select zk.require_cross_project_canonical_pit(
 'total-rasyo-bootstrap-v1',
 'zxc28tarik/TOTAL-RASYO-HESAPLAYICI',
 '445e9a7cb788124a52fd4ac171f3e16e6c67137e',
 'data/backtest_sources/m3_source_package/index_closes.csv.gz'
);
