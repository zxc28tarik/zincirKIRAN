-- Zincir Kıran — Current BIST roster/share-state bootstrap schema v0.1

create table zk.current_bootstrap_artifacts (
    artifact_id text primary key,
    source_repository text not null,
    source_commit text not null,
    source_path text not null,
    sha256 text not null,
    authority text not null,
    row_count integer not null,
    scope_note text not null,
    created_at timestamptz not null default now(),
    constraint current_bootstrap_commit_chk check (source_commit ~ '^[0-9a-f]{40}$'),
    constraint current_bootstrap_sha_chk check (sha256 ~ '^[0-9a-f]{64}$'),
    constraint current_bootstrap_authority_chk check (
        authority in (
            'CURRENT_ROSTER_DISCOVERY_ONLY',
            'CURRENT_SHARE_STATE_EVIDENCE',
            'CURRENT_MARKET_SNAPSHOT'
        )
    ),
    constraint current_bootstrap_rows_chk check (row_count > 0)
);

create function zk.reject_current_bootstrap_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'current bootstrap records are append-only';
end;
$fn$;

create trigger current_bootstrap_immutable_trg
before update or delete on zk.current_bootstrap_artifacts
for each row execute function zk.reject_current_bootstrap_mutation();

create function zk.reject_current_artifact_for_historical_use(p_artifact_id text)
returns void
language plpgsql
as $fn$
begin
    if exists (select 1 from zk.current_bootstrap_artifacts where artifact_id=p_artifact_id) then
        raise exception 'current bootstrap artifact cannot be used for historical backfill';
    end if;
    raise exception 'current bootstrap artifact is not registered';
end;
$fn$;
