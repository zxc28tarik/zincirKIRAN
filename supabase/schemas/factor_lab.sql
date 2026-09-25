-- Zincir Kıran — Factor Laboratory schema v0.1

create table zk.factor_experiments (
    experiment_id text primary key,
    factor_id text not null,
    factor_definition_version text not null,
    horizon_days integer not null,
    data_snapshot_id text not null,
    universe_rule_version text not null,
    quantile_count integer not null,
    cost_model_id text not null,
    hypothesis text not null,
    expected_direction text not null,
    preregistered_at timestamptz not null,
    constraint factor_experiments_factor_fk
        foreign key (factor_id, factor_definition_version)
        references zk.factor_registry(factor_id, definition_version),
    constraint factor_experiments_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint factor_experiments_quantiles_chk
        check (quantile_count >= 2),
    constraint factor_experiments_direction_chk
        check (expected_direction in (
            'HIGHER_IS_BETTER', 'LOWER_IS_BETTER', 'CONTEXTUAL', 'UNDECIDED'
        )),
    constraint factor_experiments_text_chk
        check (
            length(trim(experiment_id)) > 0
            and length(trim(data_snapshot_id)) > 0
            and length(trim(universe_rule_version)) > 0
            and length(trim(cost_model_id)) > 0
            and length(trim(hypothesis)) > 0
        )
);

create function zk.reject_factor_experiment_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'factor experiments are pre-registered and immutable';
end;
$$;

create trigger factor_experiments_immutable_trg
before update or delete on zk.factor_experiments
for each row execute function zk.reject_factor_experiment_mutation();

create table zk.factor_lab_results (
    experiment_id text primary key references zk.factor_experiments(experiment_id),
    evaluated_at timestamptz not null default now(),
    total_periods integer not null,
    valid_ic_periods integer not null,
    mean_ic numeric,
    icir numeric,
    mean_coverage numeric not null,
    monotonicity numeric,
    top_vs_market numeric,
    bottom_vs_market numeric,
    top_minus_bottom numeric,
    average_turnover numeric,
    gross_spread numeric,
    cost_adjusted_spread numeric,
    p_value numeric,
    q_value numeric,
    notes text,
    constraint factor_lab_results_periods_chk check (
        total_periods >= 0
        and valid_ic_periods >= 0
        and valid_ic_periods <= total_periods
    ),
    constraint factor_lab_results_coverage_chk check (
        mean_coverage >= 0 and mean_coverage <= 1
    ),
    constraint factor_lab_results_turnover_chk check (
        average_turnover is null or (average_turnover >= 0 and average_turnover <= 1)
    ),
    constraint factor_lab_results_p_chk check (
        p_value is null or (p_value >= 0 and p_value <= 1)
    ),
    constraint factor_lab_results_q_chk check (
        q_value is null or (q_value >= 0 and q_value <= 1)
    )
);

create table zk.factor_lab_liquidity_results (
    experiment_id text not null references zk.factor_experiments(experiment_id),
    liquidity_tier text not null,
    sample_size integer not null,
    coverage numeric not null,
    ic numeric,
    monotonicity numeric,
    top_vs_market numeric,
    bottom_vs_market numeric,
    top_minus_bottom numeric,
    primary key (experiment_id, liquidity_tier),
    constraint factor_lab_liquidity_tier_chk check (length(trim(liquidity_tier)) > 0),
    constraint factor_lab_liquidity_sample_chk check (sample_size >= 0),
    constraint factor_lab_liquidity_coverage_chk check (coverage >= 0 and coverage <= 1)
);

-- Deliberately no factor promotion/status mutation is performed by Factor Lab.
