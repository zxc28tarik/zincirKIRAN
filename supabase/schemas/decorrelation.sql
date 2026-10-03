-- Zincir Kıran — Factor De-correlation schema v0.1

create table zk.decorrelation_runs (
    run_id text primary key,
    data_snapshot_id text not null,
    universe_rule_version text not null,
    correlation_method text not null,
    minimum_overlap integer not null,
    absolute_threshold numeric not null,
    residualization_include_intercept boolean not null,
    preregistered_at timestamptz not null,
    created_at timestamptz not null default now(),
    constraint decorrelation_runs_method_chk
        check (correlation_method in ('PEARSON', 'SPEARMAN')),
    constraint decorrelation_runs_overlap_chk
        check (minimum_overlap >= 2),
    constraint decorrelation_runs_threshold_chk
        check (absolute_threshold > 0 and absolute_threshold <= 1),
    constraint decorrelation_runs_text_chk
        check (
            length(trim(run_id)) > 0
            and length(trim(data_snapshot_id)) > 0
            and length(trim(universe_rule_version)) > 0
        )
);

create function zk.reject_decorrelation_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'de-correlation records are append-only';
end;
$$;

create trigger decorrelation_runs_immutable_trg
before update or delete on zk.decorrelation_runs
for each row execute function zk.reject_decorrelation_mutation();

create table zk.decorrelation_pair_results (
    run_id text not null references zk.decorrelation_runs(run_id),
    left_factor_id text not null,
    left_definition_version text not null,
    right_factor_id text not null,
    right_definition_version text not null,
    statistical_state text not null,
    correlation numeric,
    overlap_count integer not null,
    concept_edge boolean not null default false,
    created_at timestamptz not null default now(),
    primary key (
        run_id,
        left_factor_id,
        left_definition_version,
        right_factor_id,
        right_definition_version
    ),
    constraint decorrelation_pair_left_factor_fk
        foreign key (left_factor_id, left_definition_version)
        references zk.factor_registry(factor_id, definition_version),
    constraint decorrelation_pair_right_factor_fk
        foreign key (right_factor_id, right_definition_version)
        references zk.factor_registry(factor_id, definition_version),
    constraint decorrelation_pair_order_chk
        check (
            (left_factor_id, left_definition_version)
            < (right_factor_id, right_definition_version)
        ),
    constraint decorrelation_pair_state_chk
        check (statistical_state in (
            'REDUNDANCY_CANDIDATE', 'BELOW_THRESHOLD', 'UNKNOWN'
        )),
    constraint decorrelation_pair_overlap_chk
        check (overlap_count >= 0),
    constraint decorrelation_pair_correlation_chk
        check (correlation is null or (correlation >= -1 and correlation <= 1)),
    constraint decorrelation_pair_unknown_chk
        check (
            (statistical_state = 'UNKNOWN' and correlation is null)
            or (statistical_state <> 'UNKNOWN' and correlation is not null)
        )
);

create trigger decorrelation_pair_results_immutable_trg
before update or delete on zk.decorrelation_pair_results
for each row execute function zk.reject_decorrelation_mutation();

create table zk.decorrelation_components (
    run_id text not null references zk.decorrelation_runs(run_id),
    component_no integer not null,
    factor_id text not null,
    definition_version text not null,
    created_at timestamptz not null default now(),
    primary key (run_id, component_no, factor_id, definition_version),
    constraint decorrelation_components_factor_fk
        foreign key (factor_id, definition_version)
        references zk.factor_registry(factor_id, definition_version),
    constraint decorrelation_components_no_chk
        check (component_no >= 1),
    unique (run_id, factor_id, definition_version)
);

create trigger decorrelation_components_immutable_trg
before update or delete on zk.decorrelation_components
for each row execute function zk.reject_decorrelation_mutation();

create table zk.decorrelation_residualization_results (
    run_id text not null references zk.decorrelation_runs(run_id),
    target_factor_id text not null,
    target_definition_version text not null,
    explanatory_factor_id text not null,
    explanatory_definition_version text not null,
    residualization_state text not null,
    overlap_count integer not null,
    intercept numeric,
    beta numeric,
    created_at timestamptz not null default now(),
    primary key (
        run_id,
        target_factor_id,
        target_definition_version,
        explanatory_factor_id,
        explanatory_definition_version
    ),
    constraint decorrelation_residual_target_fk
        foreign key (target_factor_id, target_definition_version)
        references zk.factor_registry(factor_id, definition_version),
    constraint decorrelation_residual_explanatory_fk
        foreign key (explanatory_factor_id, explanatory_definition_version)
        references zk.factor_registry(factor_id, definition_version),
    constraint decorrelation_residual_not_self_chk
        check (
            (target_factor_id, target_definition_version)
            <> (explanatory_factor_id, explanatory_definition_version)
        ),
    constraint decorrelation_residual_state_chk
        check (residualization_state in (
            'ESTIMATED', 'INSUFFICIENT_OVERLAP', 'DEGENERATE_EXPLANATORY'
        )),
    constraint decorrelation_residual_overlap_chk
        check (overlap_count >= 0),
    constraint decorrelation_residual_coefficients_chk
        check (
            (residualization_state = 'ESTIMATED' and intercept is not null and beta is not null)
            or (residualization_state <> 'ESTIMATED' and intercept is null and beta is null)
        )
);

create trigger decorrelation_residualization_results_immutable_trg
before update or delete on zk.decorrelation_residualization_results
for each row execute function zk.reject_decorrelation_mutation();

create index decorrelation_pair_run_state_idx
    on zk.decorrelation_pair_results(run_id, statistical_state, concept_edge);

create index decorrelation_component_run_idx
    on zk.decorrelation_components(run_id, component_no);
