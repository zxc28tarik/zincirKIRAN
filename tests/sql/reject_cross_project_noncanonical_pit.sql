\set ON_ERROR_STOP on
insert into zk.cross_project_manifests values ('reject-auth','X',now());
insert into zk.cross_project_artifacts (
 manifest_id,source_repository,source_commit,source_path,evidence_domain,
 authority,coverage_note
) values (
 'reject-auth','owner/repo',repeat('a',40),'x.json','FINANCIALS',
 'DISCOVERY_ONLY','not canonical'
);
select zk.require_cross_project_canonical_pit(
 'reject-auth','owner/repo',repeat('a',40),'x.json'
);
