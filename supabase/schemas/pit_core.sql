-- Zincir Kıran — declarative PIT core schema v0.1
-- Internal schema: intentionally not exposed through Supabase Data API.

create schema if not exists zk;

revoke all on schema zk from public;

-- Supabase-specific role revokes are intentionally deferred until a remote
-- Supabase project exists. PUBLIC has no access to this internal schema.

create table if not exists zk.source_registry (
    source_id uuid primary key default gen_random_uuid(),
    name text not null unique,
    source_type text not null,
    base_url text,
    license_notes text,
    timestamp_quality text not null default 'UNKNOWN',
    revision_policy text,
    priority smallint not null default 100,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists zk.companies (
    company_id uuid primary key default gen_random_uuid(),
    legal_name text not null,
    sector text,
    industry text,
    company_type text,
    first_trade_date date,
    last_trade_date date,
    status text not null default 'ACTIVE',
    primary_source_id uuid references zk.source_registry(source_id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint companies_trade_dates_chk
        check (last_trade_date is null or first_trade_date is null or last_trade_date >= first_trade_date)
);

create table if not exists zk.securities (
    security_id uuid primary key default gen_random_uuid(),
    company_id uuid not null references zk.companies(company_id),
    exchange text not null default 'BIST',
    security_type text not null default 'EQUITY',
    first_trade_date date,
    last_trade_date date,
    created_at timestamptz not null default now(),
    constraint securities_trade_dates_chk
        check (last_trade_date is null or first_trade_date is null or last_trade_date >= first_trade_date)
);

create index if not exists securities_company_idx
    on zk.securities(company_id);

create table if not exists zk.security_identifiers (
    security_identifier_id bigint generated always as identity primary key,
    security_id uuid not null references zk.securities(security_id),
    ticker text not null,
    isin text,
    valid_from date not null,
    valid_to date,
    source_id uuid references zk.source_registry(source_id),
    created_at timestamptz not null default now(),
    constraint security_identifiers_validity_chk
        check (valid_to is null or valid_to >= valid_from),
    unique (security_id, ticker, valid_from)
);

create index if not exists security_identifiers_ticker_idx
    on zk.security_identifiers(ticker, valid_from desc);

create table if not exists zk.prices (
    price_id bigint generated always as identity primary key,
    security_id uuid not null references zk.securities(security_id),
    trade_date date not null,
    open numeric(24,8),
    high numeric(24,8),
    low numeric(24,8),
    close numeric(24,8) not null,
    volume numeric(30,4),
    turnover_value numeric(30,4),
    currency text not null default 'TRY',
    source_id uuid not null references zk.source_registry(source_id),
    revision_id text not null default 'original',
    reported_at timestamptz,
    available_at timestamptz not null,
    ingested_at timestamptz not null default now(),
    quality_flag text not null default 'VERIFIED',
    unique (security_id, trade_date, source_id, revision_id)
);

create index if not exists prices_security_trade_date_idx
    on zk.prices(security_id, trade_date desc);

create index if not exists prices_available_at_idx
    on zk.prices(available_at);

create table if not exists zk.financial_facts (
    financial_fact_id bigint generated always as identity primary key,
    company_id uuid not null references zk.companies(company_id),
    statement_type text not null,
    metric_id text not null,
    period_start date,
    period_end date not null,
    fiscal_period text,
    value numeric(38,10),
    currency text,
    unit text,
    reported_at timestamptz,
    available_at timestamptz not null,
    revision_id text not null,
    source_id uuid not null references zk.source_registry(source_id),
    reporting_standard text,
    inflation_adjusted boolean,
    restatement_status text,
    original_period text,
    publication_date date,
    revision_date date,
    quality_flag text not null default 'VERIFIED',
    ingested_at timestamptz not null default now()
);

create unique index if not exists financial_facts_identity_uidx
    on zk.financial_facts(
        company_id,
        metric_id,
        period_end,
        coalesce(fiscal_period, ''),
        source_id,
        revision_id
    );

create index if not exists financial_facts_pit_lookup_idx
    on zk.financial_facts(company_id, metric_id, period_end desc, available_at desc);

create index if not exists financial_facts_available_at_idx
    on zk.financial_facts(available_at);

create table if not exists zk.financial_revisions (
    financial_revision_id bigint generated always as identity primary key,
    financial_fact_id bigint not null references zk.financial_facts(financial_fact_id),
    supersedes_financial_fact_id bigint references zk.financial_facts(financial_fact_id),
    revision_id text not null,
    reason text,
    announced_at timestamptz,
    available_at timestamptz not null,
    source_id uuid not null references zk.source_registry(source_id),
    created_at timestamptz not null default now(),
    constraint financial_revisions_not_self_chk
        check (
            supersedes_financial_fact_id is null
            or supersedes_financial_fact_id <> financial_fact_id
        ),
    unique (financial_fact_id, revision_id, source_id)
);

create index if not exists financial_revisions_available_at_idx
    on zk.financial_revisions(available_at);

create table if not exists zk.corporate_actions (
    corporate_action_id bigint generated always as identity primary key,
    security_id uuid not null references zk.securities(security_id),
    action_type text not null,
    announcement_at timestamptz,
    ex_date date,
    record_date date,
    payment_date date,
    ratio numeric(30,12),
    cash_amount numeric(30,8),
    currency text,
    source_id uuid not null references zk.source_registry(source_id),
    available_at timestamptz not null,
    quality_flag text not null default 'VERIFIED',
    ingested_at timestamptz not null default now()
);

create index if not exists corporate_actions_security_date_idx
    on zk.corporate_actions(security_id, ex_date desc);

create index if not exists corporate_actions_available_at_idx
    on zk.corporate_actions(available_at);

create table if not exists zk.shares_history (
    shares_history_id bigint generated always as identity primary key,
    company_id uuid not null references zk.companies(company_id),
    effective_from date not null,
    effective_to date,
    shares_outstanding numeric(30,4),
    free_float_shares numeric(30,4),
    free_float_ratio numeric(12,8),
    source_id uuid not null references zk.source_registry(source_id),
    reported_at timestamptz,
    available_at timestamptz not null,
    quality_flag text not null default 'VERIFIED',
    ingested_at timestamptz not null default now(),
    constraint shares_history_validity_chk
        check (effective_to is null or effective_to >= effective_from),
    constraint shares_history_free_float_ratio_chk
        check (free_float_ratio is null or (free_float_ratio >= 0 and free_float_ratio <= 1))
);

create index if not exists shares_history_company_date_idx
    on zk.shares_history(company_id, effective_from desc, available_at desc);

create table if not exists zk.universe_history (
    trade_date date not null,
    security_id uuid not null references zk.securities(security_id),
    is_investable boolean not null,
    reason_code text,
    liquidity_tier text,
    source_id uuid references zk.source_registry(source_id),
    model_rule_version text not null,
    available_at timestamptz not null,
    created_at timestamptz not null default now(),
    primary key (trade_date, security_id, model_rule_version)
);

create index if not exists universe_history_investable_idx
    on zk.universe_history(trade_date, is_investable, liquidity_tier);

-- No grants are made to anon/authenticated. This schema is internal by design.
