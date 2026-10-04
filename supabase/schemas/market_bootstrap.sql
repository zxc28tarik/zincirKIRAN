-- Zincir Kıran — Historical Market Bootstrap schema v0.1

create table zk.market_bootstrap_artifacts (
    artifact_id text primary key,
    source_repository text not null,
    source_commit text not null,
    source_path text not null,
    sha256 text not null,
    authority text not null,
    row_count bigint,
    coverage_start text,
    coverage_end text,
    scope_note text not null,
    created_at timestamptz not null default now(),
    constraint market_bootstrap_commit_chk check (source_commit ~ '^[0-9a-f]{40}$'),
    constraint market_bootstrap_sha_chk check (sha256 ~ '^[0-9a-f]{64}$'),
    constraint market_bootstrap_authority_chk check (
        authority in (
            'VALIDATED_DERIVED_MARKET_DATA',
            'VALIDATED_EXECUTION_PANEL',
            'OFFICIAL_BORSA_EVIDENCE'
        )
    ),
    constraint market_bootstrap_rows_chk check (row_count is null or row_count > 0)
);

create function zk.reject_market_bootstrap_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'market bootstrap records are append-only';
end;
$fn$;

create trigger market_bootstrap_immutable_trg
before update or delete on zk.market_bootstrap_artifacts
for each row execute function zk.reject_market_bootstrap_mutation();

create function zk.require_official_borsa_market_artifact(p_artifact_id text)
returns void
language plpgsql
as $fn$
declare
    auth text;
begin
    select authority into auth
      from zk.market_bootstrap_artifacts
     where artifact_id = p_artifact_id;

    if auth is null then
        raise exception 'market bootstrap artifact is not registered';
    end if;
    if auth <> 'OFFICIAL_BORSA_EVIDENCE' then
        raise exception 'market bootstrap artifact is not official Borsa evidence';
    end if;
end;
$fn$;
