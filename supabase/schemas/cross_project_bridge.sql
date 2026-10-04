-- Zincir Kıran — Cross-project evidence bridge schema v0.1
-- Reuses evidence by exact repo/commit/path/hash with explicit authority.

create table zk.cross_project_manifests (
    manifest_id text primary key,
    source_project text not null,
    created_at timestamptz not null default now(),
    constraint cross_project_manifest_text_chk check (
        length(trim(manifest_id)) > 0
        and length(trim(source_project)) > 0
    )
);

create function zk.reject_cross_project_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'cross-project evidence records are append-only';
end;
$fn$;

create trigger cross_project_manifests_immutable_trg
before update or delete on zk.cross_project_manifests
for each row execute function zk.reject_cross_project_mutation();

create table zk.cross_project_artifacts (
    manifest_id text not null references zk.cross_project_manifests(manifest_id),
    source_repository text not null,
    source_commit text not null,
    source_path text not null,
    source_pr integer,
    evidence_domain text not null,
    expected_sha256 text,
    authority text not null,
    coverage_note text not null,
    created_at timestamptz not null default now(),
    primary key (manifest_id, source_repository, source_commit, source_path),
    constraint cross_project_commit_chk check (source_commit ~ '^[0-9a-f]{40}$'),
    constraint cross_project_sha_chk check (
        expected_sha256 is null or expected_sha256 ~ '^[0-9a-f]{64}$'
    ),
    constraint cross_project_domain_chk check (
        evidence_domain in (
            'PRICES','VOLUME','FINANCIALS','PUBLICATION_TIMESTAMPS',
            'CORPORATE_ACTIONS','UNIVERSE_HISTORY'
        )
    ),
    constraint cross_project_authority_chk check (
        authority in (
            'CANONICAL_PIT','RAW_EVIDENCE_ONLY','POSITIVE_EVENT_ONLY',
            'DISCOVERY_ONLY','FORBIDDEN'
        )
    ),
    constraint cross_project_text_chk check (
        length(trim(source_repository)) > 0
        and length(trim(source_path)) > 0
        and length(trim(coverage_note)) > 0
    )
);

create trigger cross_project_artifacts_immutable_trg
before update or delete on zk.cross_project_artifacts
for each row execute function zk.reject_cross_project_mutation();

create table zk.cross_project_prohibited_products (
    manifest_id text not null references zk.cross_project_manifests(manifest_id),
    product_code text not null,
    created_at timestamptz not null default now(),
    primary key (manifest_id, product_code),
    constraint cross_project_product_text_chk check (length(trim(product_code)) > 0)
);

create trigger cross_project_prohibited_products_immutable_trg
before update or delete on zk.cross_project_prohibited_products
for each row execute function zk.reject_cross_project_mutation();

create function zk.require_cross_project_canonical_pit(
    p_manifest_id text,
    p_source_repository text,
    p_source_commit text,
    p_source_path text
)
returns void
language plpgsql
as $fn$
declare
    auth text;
begin
    select authority into auth
      from zk.cross_project_artifacts
     where manifest_id = p_manifest_id
       and source_repository = p_source_repository
       and source_commit = p_source_commit
       and source_path = p_source_path;

    if auth is null then
        raise exception 'cross-project artifact is not registered';
    end if;
    if auth <> 'CANONICAL_PIT' then
        raise exception 'cross-project artifact is not authorized for canonical PIT';
    end if;
end;
$fn$;
