-- Zincir Kıran — Experimental Factor Lab Run schema v0.1

create table zk.experimental_factor_lab_runs (
    run_id text primary key,
    dataset_id text not null,
    factor_id text not null,
    factor_definition_version text not null,
    horizon_days integer not null,
    direction text not null,
    quantile_count integer not null,
    cost_model_id text not null,
    preregistered_at timestamptz not null,
    executed_at timestamptz not null,
    authority text not null default 'EXPERIMENTAL_VERSION_RISK',
    created_at timestamptz not null default now(),
    constraint experimental_lab_horizon_chk check (horizon_days in (20,60,120,252)),
    constraint experimental_lab_direction_chk check (
        direction in ('HIGHER_IS_BETTER','LOWER_IS_BETTER')
    ),
    constraint experimental_lab_quantile_chk check (quantile_count >= 2),
    constraint experimental_lab_time_chk check (executed_at > preregistered_at),
    constraint experimental_lab_authority_chk check (
        authority = 'EXPERIMENTAL_VERSION_RISK'
    )
);

create function zk.reject_experimental_lab_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'experimental Factor-Lab records are append-only';
end;
$fn$;

create trigger experimental_factor_lab_runs_immutable_trg
before update or delete on zk.experimental_factor_lab_runs
for each row execute function zk.reject_experimental_lab_mutation();

create table zk.experimental_factor_lab_periods (
    run_id text not null references zk.experimental_factor_lab_runs(run_id),
    as_of date not null,
    sample_size integer,
    total_observations integer,
    coverage numeric,
    ic numeric,
    monotonicity numeric,
    top_vs_market numeric,
    bottom_vs_market numeric,
    top_minus_bottom numeric,
    unavailable_reason text,
    created_at timestamptz not null default now(),
    primary key (run_id, as_of),
    constraint experimental_lab_period_availability_chk check (
        (
            unavailable_reason is null
            and sample_size is not null
            and total_observations is not null
            and coverage is not null
        )
        or (
            unavailable_reason is not null
            and length(trim(unavailable_reason)) > 0
            and sample_size is null
            and total_observations is null
            and coverage is null
        )
    ),
    constraint experimental_lab_period_coverage_chk check (
        coverage is null or coverage between 0 and 1
    )
);

create trigger experimental_factor_lab_periods_immutable_trg
before update or delete on zk.experimental_factor_lab_periods
for each row execute function zk.reject_experimental_lab_mutation();

create table zk.experimental_factor_lab_summaries (
    run_id text primary key references zk.experimental_factor_lab_runs(run_id),
    valid_periods integer not null,
    total_periods integer not null,
    mean_ic numeric,
    icir numeric,
    mean_coverage numeric not null,
    mean_top_vs_market numeric,
    mean_top_minus_bottom numeric,
    created_at timestamptz not null default now(),
    constraint experimental_lab_summary_periods_chk check (
        valid_periods >= 0 and total_periods > 0 and valid_periods <= total_periods
    ),
    constraint experimental_lab_summary_coverage_chk check (
        mean_coverage between 0 and 1
    )
);

create trigger experimental_factor_lab_summaries_immutable_trg
before update or delete on zk.experimental_factor_lab_summaries
for each row execute function zk.reject_experimental_lab_mutation();

create table zk.experimental_factor_lab_liquidity_summaries (
    run_id text not null references zk.experimental_factor_lab_runs(run_id),
    tier text not null,
    valid_periods integer not null,
    total_periods integer not null,
    mean_ic numeric,
    icir numeric,
    mean_top_vs_market numeric,
    mean_top_minus_bottom numeric,
    created_at timestamptz not null default now(),
    primary key (run_id, tier),
    constraint experimental_lab_liquidity_tier_chk check (length(trim(tier)) > 0),
    constraint experimental_lab_liquidity_periods_chk check (
        valid_periods >= 0 and total_periods > 0 and valid_periods <= total_periods
    )
);

create trigger experimental_factor_lab_liquidity_immutable_trg
before update or delete on zk.experimental_factor_lab_liquidity_summaries
for each row execute function zk.reject_experimental_lab_mutation();

create function zk.reject_experimental_lab_promotion(p_run_id text)
returns void
language plpgsql
as $fn$
begin
    if exists (select 1 from zk.experimental_factor_lab_runs where run_id=p_run_id) then
        raise exception 'experimental Factor-Lab run cannot authorize promotion';
    end if;
    raise exception 'experimental Factor-Lab run is not registered';
end;
$fn$;
