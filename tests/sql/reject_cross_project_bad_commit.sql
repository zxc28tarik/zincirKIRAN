\set ON_ERROR_STOP on
insert into zk.cross_project_manifests values ('reject-sha','X',now());
insert into zk.cross_project_artifacts (
 manifest_id,source_repository,source_commit,source_path,evidence_domain,
 authority,coverage_note
) values (
 'reject-sha','owner/repo','short','x.json','PRICES',
 'CANONICAL_PIT','bad sha'
);
