-- Zincir Kıran — Baselines schema v0.1

create table zk.baseline_definitions (
    baseline_id text not null,
    definition_version text not null,
    formula text not null,
    parameters jsonb not null default '{}'::jsonb,
    baseline_role text not null default 'COMPARATOR',
    created_at timestamptz not null default now(),
    primary key (baseline_id, definition_version),
    constraint baseline_definitions_id_chk
        check (baseline_id in (
            'MARKET_BENCHMARK',
            'EQUAL_WEIGHT',
            'SIMPLE_VALUE',
            'SIMPLE_MOMENTUM',
            'QVM',
            'TURKISH_FACTOR',
            'TOTAL_RASYO'
        )),
    constraint baseline_definitions_version_chk
        check (length(trim(definition_version)) > 0),
    constraint baseline_definitions_formula_chk
        check (length(trim(formula)) > 0),
    constraint baseline_definitions_role_chk
        check (baseline_role in ('COMPARATOR', 'FAILED_REFERENCE')),
    constraint baseline_total_rasyo_role_chk
        check (
            baseline_id <> 'TOTAL_RASYO'
            or baseline_role = 'FAILED_REFERENCE'
        )
);

create function zk.reject_baseline_definition_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'baseline definitions are append-only; create a new definition_version';
end;
$$;

create trigger baseline_definitions_immutable_trg
before update or delete on zk.baseline_definitions
for each row execute function zk.reject_baseline_definition_mutation();

create table zk.baseline_runs (
    run_id uuid primary key default gen_random_uuid(),
    baseline_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    data_snapshot_id text not null,
    universe_rule_version text not null,
    rebalance_specification text not null,
    created_at timestamptz not null default now(),
    constraint baseline_runs_definition_fk
        foreign key (baseline_id, definition_version)
        references zk.baseline_definitions(baseline_id, definition_version),
    constraint baseline_runs_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint baseline_runs_snapshot_chk
        check (length(trim(data_snapshot_id)) > 0),
    constraint baseline_runs_universe_chk
        check (length(trim(universe_rule_version)) > 0),
    constraint baseline_runs_rebalance_chk
        check (length(trim(rebalance_specification)) > 0)
);

create index baseline_runs_lookup_idx
    on zk.baseline_runs(baseline_id, definition_version, horizon_days, created_at desc);
