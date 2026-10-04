\set ON_ERROR_STOP on
insert into zk.cross_project_manifests values ('reject-x','X',now());
update zk.cross_project_manifests set source_project='Y' where manifest_id='reject-x';
