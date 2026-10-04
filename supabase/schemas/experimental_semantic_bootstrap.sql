-- Zincir Kıran — Experimental Semantic Financial Facts Bootstrap schema v0.1

create table zk.experimental_semantic_corpora (
    corpus_id text primary key,
    source_repository text not null,
    source_commit text not null,
    authority text not null,
    total_report_count integer not null,
    total_fact_count integer not null,
    own_period_visible_cells integer not null,
    historical_cells integer not null,
    authoritative_claim_allowed boolean not null default false,
    created_at timestamptz not null default now(),
    constraint experimental_semantic_commit_chk check (source_commit ~ '^[0-9a-f]{40}$'),
    constraint experimental_semantic_authority_chk check (
        authority = 'EXPERIMENTAL_VERSION_RISK'
    ),
    constraint experimental_semantic_no_authoritative_chk check (
        authoritative_claim_allowed = false
    ),
    constraint experimental_semantic_counts_chk check (
        total_report_count > 0
        and total_fact_count > 0
        and historical_cells > 0
        and own_period_visible_cells between 0 and historical_cells
    )
);

create function zk.reject_experimental_semantic_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'experimental semantic records are append-only';
end;
$fn$;

create trigger experimental_semantic_corpora_immutable_trg
before update or delete on zk.experimental_semantic_corpora
for each row execute function zk.reject_experimental_semantic_mutation();

create table zk.experimental_semantic_artifacts (
    corpus_id text not null references zk.experimental_semantic_corpora(corpus_id),
    artifact_id text not null,
    source_path text not null,
    sha256 text not null,
    report_count integer not null,
    fact_count integer not null,
    authority text not null,
    scope_note text not null,
    created_at timestamptz not null default now(),
    primary key (corpus_id, artifact_id),
    constraint experimental_semantic_artifact_sha_chk check (sha256 ~ '^[0-9a-f]{64}$'),
    constraint experimental_semantic_artifact_counts_chk check (
        report_count > 0 and fact_count > 0
    ),
    constraint experimental_semantic_artifact_authority_chk check (
        authority = 'EXPERIMENTAL_VERSION_RISK'
    )
);

create trigger experimental_semantic_artifacts_immutable_trg
before update or delete on zk.experimental_semantic_artifacts
for each row execute function zk.reject_experimental_semantic_mutation();

create table zk.experimental_semantic_risks (
    corpus_id text not null references zk.experimental_semantic_corpora(corpus_id),
    risk_id text not null,
    created_at timestamptz not null default now(),
    primary key (corpus_id, risk_id),
    constraint experimental_semantic_risk_text_chk check (length(trim(risk_id)) > 0)
);

create trigger experimental_semantic_risks_immutable_trg
before update or delete on zk.experimental_semantic_risks
for each row execute function zk.reject_experimental_semantic_mutation();

create function zk.require_experimental_semantic_authority(
    p_corpus_id text,
    p_requested_authority text
)
returns void
language plpgsql
as $fn$
declare
    auth text;
begin
    select authority into auth
      from zk.experimental_semantic_corpora
     where corpus_id = p_corpus_id;

    if auth is null then
        raise exception 'experimental semantic corpus is not registered';
    end if;
    if p_requested_authority <> 'EXPERIMENTAL_VERSION_RISK' then
        raise exception 'experimental semantic corpus cannot be promoted to authoritative evidence';
    end if;
end;
$fn$;
