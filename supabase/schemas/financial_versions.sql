-- Zincir Kıran — Financial Revision / PIT Version Authority schema v0.1

create table zk.financial_version_chains (
    ticker text not null,
    period_end date not null,
    enumeration_complete boolean not null,
    authority text not null,
    created_at timestamptz not null default now(),
    primary key (ticker, period_end),
    constraint financial_version_authority_chk check (
        authority in ('AUTHORITATIVE_PIT','EXPERIMENTAL_VERSION_RISK','BULK_LATEST_ONLY')
    ),
    constraint financial_version_authoritative_complete_chk check (
        authority <> 'AUTHORITATIVE_PIT' or enumeration_complete = true
    ),
    constraint financial_version_ticker_chk check (length(trim(ticker)) > 0)
);

create function zk.reject_financial_version_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'financial version records are append-only';
end;
$fn$;

create trigger financial_version_chains_immutable_trg
before update or delete on zk.financial_version_chains
for each row execute function zk.reject_financial_version_mutation();

create table zk.financial_versions (
    ticker text not null,
    period_end date not null,
    disclosure_id text not null,
    published_at timestamptz not null,
    raw_sha256 text not null,
    version_sequence integer not null,
    version_tag text not null,
    supersedes_disclosure_id text,
    created_at timestamptz not null default now(),
    primary key (ticker, period_end, disclosure_id),
    foreign key (ticker, period_end)
        references zk.financial_version_chains(ticker, period_end),
    constraint financial_version_sha_chk check (raw_sha256 ~ '^[0-9a-f]{64}$'),
    constraint financial_version_sequence_chk check (version_sequence >= 1),
    constraint financial_version_text_chk check (
        length(trim(disclosure_id)) > 0
        and length(trim(version_tag)) > 0
    ),
    constraint financial_version_self_supersede_chk check (
        supersedes_disclosure_id is null or supersedes_disclosure_id <> disclosure_id
    )
);

create unique index financial_versions_sequence_uniq
on zk.financial_versions(ticker, period_end, version_sequence);

create trigger financial_versions_immutable_trg
before update or delete on zk.financial_versions
for each row execute function zk.reject_financial_version_mutation();

create function zk.require_authoritative_financial_chain(
    p_ticker text,
    p_period_end date
)
returns void
language plpgsql
as $fn$
declare
    auth text;
    complete boolean;
begin
    select authority, enumeration_complete
      into auth, complete
      from zk.financial_version_chains
     where ticker = p_ticker
       and period_end = p_period_end;

    if auth is null then
        raise exception 'financial version chain is not registered';
    end if;

    if auth <> 'AUTHORITATIVE_PIT' or complete is distinct from true then
        raise exception 'financial version chain is not authorized for authoritative PIT';
    end if;
end;
$fn$;

create function zk.select_financial_version_at_cutoff(
    p_ticker text,
    p_period_end date,
    p_cutoff_at timestamptz
)
returns text
language plpgsql
as $fn$
declare
    chosen text;
begin
    perform zk.require_authoritative_financial_chain(p_ticker, p_period_end);

    select disclosure_id into chosen
      from zk.financial_versions
     where ticker = p_ticker
       and period_end = p_period_end
       and published_at <= p_cutoff_at
     order by published_at desc, version_sequence desc, disclosure_id desc
     limit 1;

    return chosen;
end;
$fn$;
