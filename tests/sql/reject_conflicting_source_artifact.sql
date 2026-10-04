\set ON_ERROR_STOP on
insert into zk.source_artifacts (
 artifact_id,source_id,source_url,domain,retrieved_at,content_sha256,byte_size,logical_key
) values
 ('a1','kap','https://kap.org.tr','FINANCIALS',now(),repeat('a',64),1,'same:key'),
 ('a2','kap','https://kap.org.tr','FINANCIALS',now(),repeat('b',64),1,'same:key');
