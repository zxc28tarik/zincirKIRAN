-- Zincir Kıran — Analyst Estimates / Revisions schema v0.1

create table zk.analyst_estimate_snapshots (
    ticker text not null,
    fiscal_period_end timestamptz not null,
    estimate_at timestamptz not null,
    authority text not null,
    eps_consensus numeric,
    revenue_consensus numeric,
    analyst_count integer,
    eps_high numeric,
    eps_low numeric,
    revenue_high numeric,
    revenue_low numeric,
    currency text,
    source text not null,
    created_at timestamptz not null default now(),
    primary key (ticker, fiscal_period_end, estimate_at, source),
    constraint analyst_estimate_authority_chk check (
        authority in ('HISTORICAL_PIT','CURRENT_ONLY')
    ),
    constraint analyst_estimate_count_chk check (
        analyst_count is null or analyst_count >= 0
    ),
    constraint analyst_estimate_text_chk check (
        length(trim(ticker)) > 0 and length(trim(source)) > 0
    )
);

create function zk.reject_analyst_estimate_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'analyst estimate records are append-only';
end;
$fn$;

create trigger analyst_estimate_snapshots_immutable_trg
before update or delete on zk.analyst_estimate_snapshots
for each row execute function zk.reject_analyst_estimate_mutation();

create table zk.analyst_estimate_revisions (
    ticker text not null,
    fiscal_period_end timestamptz not null,
    earlier_at timestamptz not null,
    later_at timestamptz not null,
    eps_revision numeric,
    revenue_revision numeric,
    source text not null,
    created_at timestamptz not null default now(),
    primary key (ticker, fiscal_period_end, earlier_at, later_at, source),
    constraint analyst_revision_time_chk check (earlier_at < later_at),
    foreign key (ticker, fiscal_period_end, earlier_at, source)
        references zk.analyst_estimate_snapshots(ticker, fiscal_period_end, estimate_at, source),
    foreign key (ticker, fiscal_period_end, later_at, source)
        references zk.analyst_estimate_snapshots(ticker, fiscal_period_end, estimate_at, source)
);

create trigger analyst_estimate_revisions_immutable_trg
before update or delete on zk.analyst_estimate_revisions
for each row execute function zk.reject_analyst_estimate_mutation();

create function zk.validate_analyst_revision_authority()
returns trigger language plpgsql as $fn$
declare
    earlier_auth text;
    later_auth text;
begin
    select authority into earlier_auth
      from zk.analyst_estimate_snapshots
     where ticker=new.ticker
       and fiscal_period_end=new.fiscal_period_end
       and estimate_at=new.earlier_at
       and source=new.source;

    select authority into later_auth
      from zk.analyst_estimate_snapshots
     where ticker=new.ticker
       and fiscal_period_end=new.fiscal_period_end
       and estimate_at=new.later_at
       and source=new.source;

    if earlier_auth <> 'HISTORICAL_PIT' or later_auth <> 'HISTORICAL_PIT' then
        raise exception 'analyst revision requires two HISTORICAL_PIT snapshots';
    end if;

    return new;
end;
$fn$;

create trigger analyst_estimate_revisions_authority_trg
before insert on zk.analyst_estimate_revisions
for each row execute function zk.validate_analyst_revision_authority();
