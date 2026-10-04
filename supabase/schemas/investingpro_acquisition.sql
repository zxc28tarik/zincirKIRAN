-- Zincir Kıran — InvestingPro Estimates / Revisions Acquisition schema v0.1

create table zk.investingpro_export_batches (
    batch_id text primary key,
    exported_at timestamptz not null,
    filter_description text not null,
    row_count integer not null,
    content_sha256 text not null,
    authority text not null,
    created_at timestamptz not null default now(),
    constraint investingpro_batch_rows_chk check (row_count between 1 and 99),
    constraint investingpro_batch_sha_chk check (content_sha256 ~ '^[0-9a-f]{64}$'),
    constraint investingpro_batch_authority_chk check (
        authority in (
            'CURRENT_SCREENER_SNAPSHOT',
            'CURRENT_ESTIMATE_SNAPSHOT',
            'TIMESTAMPED_REVISION_HISTORY',
            'FUNDAMENTAL_CROSSCHECK'
        )
    ),
    constraint investingpro_batch_filter_chk check (length(trim(filter_description)) > 0)
);

create function zk.reject_investingpro_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'InvestingPro acquisition records are append-only';
end;
$fn$;

create trigger investingpro_export_batches_immutable_trg
before update or delete on zk.investingpro_export_batches
for each row execute function zk.reject_investingpro_mutation();

create table zk.investingpro_estimate_observations (
    ticker text not null,
    metric text not null,
    period_label text,
    observed_at timestamptz not null,
    value numeric not null,
    source_batch_id text not null references zk.investingpro_export_batches(batch_id),
    authority text not null,
    created_at timestamptz not null default now(),
    primary key (ticker, metric, period_label, observed_at, source_batch_id),
    constraint investingpro_estimate_metric_chk check (
        metric in (
            'EPS_ESTIMATE','REVENUE_ESTIMATE','EPS_REVISION','REVENUE_REVISION',
            'ANALYST_COUNT','ESTIMATE_DISPERSION','FORWARD_EPS','FORWARD_REVENUE'
        )
    ),
    constraint investingpro_estimate_authority_chk check (
        authority in ('CURRENT_ESTIMATE_SNAPSHOT','TIMESTAMPED_REVISION_HISTORY')
    ),
    constraint investingpro_estimate_ticker_chk check (length(trim(ticker)) > 0)
);

create trigger investingpro_estimate_observations_immutable_trg
before update or delete on zk.investingpro_estimate_observations
for each row execute function zk.reject_investingpro_mutation();

create function zk.require_timestamped_investingpro_history(
    p_ticker text,
    p_metric text,
    p_period_label text,
    p_observed_at timestamptz,
    p_source_batch_id text
)
returns void
language plpgsql
as $fn$
declare
    auth text;
begin
    select authority into auth
      from zk.investingpro_estimate_observations
     where ticker = p_ticker
       and metric = p_metric
       and period_label is not distinct from p_period_label
       and observed_at = p_observed_at
       and source_batch_id = p_source_batch_id;

    if auth is null then
        raise exception 'InvestingPro estimate observation is not registered';
    end if;
    if auth <> 'TIMESTAMPED_REVISION_HISTORY' then
        raise exception 'current InvestingPro estimate snapshot cannot be backfilled into historical PIT';
    end if;
end;
$fn$;

create table zk.investingpro_roster_reconciliations (
    reconciliation_id text primary key,
    kap_roster_count integer not null,
    investingpro_unique_primary_count integer not null,
    matched_tickers integer not null,
    kap_only integer not null,
    investingpro_only integer not null,
    duplicate_primary_items integer not null,
    created_at timestamptz not null default now(),
    constraint investingpro_reconcile_nonnegative_chk check (
        kap_roster_count >= 0
        and investingpro_unique_primary_count >= 0
        and matched_tickers >= 0
        and kap_only >= 0
        and investingpro_only >= 0
        and duplicate_primary_items >= 0
    ),
    constraint investingpro_reconcile_match_chk check (matched_tickers <= kap_roster_count)
);

create trigger investingpro_roster_reconciliations_immutable_trg
before update or delete on zk.investingpro_roster_reconciliations
for each row execute function zk.reject_investingpro_mutation();
