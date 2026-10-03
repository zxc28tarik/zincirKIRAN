-- Zincir Kıran — Interpretable Alpha v1 aggregation specification schema

create table zk.alpha_aggregation_specs (
    specification_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    aggregation_rule_id text not null,
    normalization_rule_id text not null,
    weight_policy_id text not null,
    coverage_rule_id text not null,
    parameters jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint alpha_aggregation_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint alpha_aggregation_text_chk
        check (
            length(trim(specification_id)) > 0
            and length(trim(definition_version)) > 0
            and length(trim(aggregation_rule_id)) > 0
            and length(trim(normalization_rule_id)) > 0
            and length(trim(weight_policy_id)) > 0
            and length(trim(coverage_rule_id)) > 0
        ),
    constraint alpha_aggregation_parameters_chk
        check (jsonb_typeof(parameters) = 'object')
);

create function zk.reject_alpha_aggregation_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'alpha aggregation specifications are append-only';
end;
$$;

create trigger alpha_aggregation_specs_immutable_trg
before update or delete on zk.alpha_aggregation_specs
for each row execute function zk.reject_alpha_aggregation_mutation();
-- Explicit factor admission provenance for Alpha v1.
create table zk.alpha_factor_admissions (
    admission_id text primary key,
    factor_id text not null,
    factor_definition_version text not null,
    horizon_days integer not null,
    decision text not null,
    factor_lab_experiment_id text not null references zk.factor_experiments(experiment_id),
    decorrelation_run_id text not null references zk.decorrelation_runs(run_id),
    decorrelation_component_no integer not null,
    rationale text not null,
    created_at timestamptz not null default now(),
    constraint alpha_factor_admissions_factor_fk
        foreign key (factor_id, factor_definition_version)
        references zk.factor_registry(factor_id, definition_version),
    constraint alpha_factor_admissions_component_fk
        foreign key (
            decorrelation_run_id, decorrelation_component_no,
            factor_id, factor_definition_version
        ) references zk.decorrelation_components(
            run_id, component_no, factor_id, definition_version
        ),
    constraint alpha_factor_admissions_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint alpha_factor_admissions_decision_chk
        check (decision in ('ADMITTED', 'REJECTED', 'UNDECIDED')),
    constraint alpha_factor_admissions_text_chk
        check (
            length(trim(admission_id)) > 0
            and length(trim(rationale)) > 0
        )
);

create function zk.validate_alpha_factor_admission_provenance()
returns trigger
language plpgsql
as $$
begin
    if not exists (
        select 1
        from zk.factor_experiments e
        where e.experiment_id = new.factor_lab_experiment_id
          and e.factor_id = new.factor_id
          and e.factor_definition_version = new.factor_definition_version
          and e.horizon_days = new.horizon_days
    ) then
        raise exception 'alpha admission does not match Factor Lab provenance';
    end if;
    return new;
end;
$$;

create trigger alpha_factor_admissions_provenance_trg
before insert on zk.alpha_factor_admissions
for each row execute function zk.validate_alpha_factor_admission_provenance();

create trigger alpha_factor_admissions_immutable_trg
before update or delete on zk.alpha_factor_admissions
for each row execute function zk.reject_alpha_aggregation_mutation();

-- Resolved per-factor weights. The policy name lives on the immutable spec;
-- these rows are the auditable resolved values, not a hard-coded production choice.
create table zk.alpha_factor_weights (
    specification_id text not null,
    definition_version text not null,
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    weight numeric not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, admission_id),
    constraint alpha_factor_weights_spec_fk
        foreign key (specification_id, definition_version)
        references zk.alpha_aggregation_specs(specification_id, definition_version),
    constraint alpha_factor_weights_value_chk
        check (
            weight <> 0
            and weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        )
);

create function zk.validate_alpha_factor_weight()
returns trigger
language plpgsql
as $$
declare
    spec_horizon integer;
    admission_horizon integer;
    admission_decision text;
    admission_run text;
    admission_component integer;
begin
    select horizon_days
      into spec_horizon
      from zk.alpha_aggregation_specs
     where specification_id = new.specification_id
       and definition_version = new.definition_version;

    select horizon_days, decision, decorrelation_run_id, decorrelation_component_no
      into admission_horizon, admission_decision, admission_run, admission_component
      from zk.alpha_factor_admissions
     where admission_id = new.admission_id;

    if admission_decision <> 'ADMITTED' then
        raise exception 'alpha weight may reference only ADMITTED factor';
    end if;
    if admission_horizon <> spec_horizon then
        raise exception 'alpha weight horizon does not match aggregation specification';
    end if;
    if exists (
        select 1
        from zk.alpha_factor_weights w
        join zk.alpha_factor_admissions a on a.admission_id = w.admission_id
        where w.specification_id = new.specification_id
          and w.definition_version = new.definition_version
          and a.decorrelation_run_id = admission_run
          and a.decorrelation_component_no = admission_component
          and w.admission_id <> new.admission_id
    ) then
        raise exception 'aggregation specification cannot assign multiple votes to one de-correlation component';
    end if;
    return new;
end;
$$;

create trigger alpha_factor_weights_validate_trg
before insert on zk.alpha_factor_weights
for each row execute function zk.validate_alpha_factor_weight();

create trigger alpha_factor_weights_immutable_trg
before update or delete on zk.alpha_factor_weights
for each row execute function zk.reject_alpha_aggregation_mutation();

create table zk.alpha_runs (
    alpha_run_id text primary key,
    specification_id text not null,
    definition_version text not null,
    security_id uuid not null references zk.securities(security_id),
    evaluated_at timestamptz not null,
    alpha_field text not null,
    status text not null,
    alpha_value numeric,
    coverage numeric not null,
    planned_absolute_weight numeric not null,
    available_absolute_weight numeric not null,
    created_at timestamptz not null default now(),
    constraint alpha_runs_spec_fk
        foreign key (specification_id, definition_version)
        references zk.alpha_aggregation_specs(specification_id, definition_version),
    constraint alpha_runs_status_chk
        check (status in ('SCORED', 'ABSTAIN_INSUFFICIENT_COVERAGE')),
    constraint alpha_runs_coverage_chk check (coverage >= 0 and coverage <= 1),
    constraint alpha_runs_weights_chk check (
        planned_absolute_weight > 0
        and available_absolute_weight >= 0
        and available_absolute_weight <= planned_absolute_weight
        and planned_absolute_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        and available_absolute_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    ),
    constraint alpha_runs_score_state_chk check (
        (status = 'SCORED' and alpha_value is not null)
        or (status = 'ABSTAIN_INSUFFICIENT_COVERAGE' and alpha_value is null)
    )
);

create function zk.validate_alpha_run_contract()
returns trigger
language plpgsql
as $$
declare
    spec_horizon integer;
    expected_field text;
begin
    select horizon_days into spec_horizon
    from zk.alpha_aggregation_specs
    where specification_id = new.specification_id
      and definition_version = new.definition_version;

    expected_field := case spec_horizon
        when 20 then 'Alpha20'
        when 60 then 'Alpha60'
        when 120 then 'Alpha120'
        when 252 then 'Alpha252'
    end;
    if new.alpha_field <> expected_field then
        raise exception 'alpha_field does not match specification horizon';
    end if;
    return new;
end;
$$;

create trigger alpha_runs_contract_trg
before insert on zk.alpha_runs
for each row execute function zk.validate_alpha_run_contract();

create trigger alpha_runs_immutable_trg
before update or delete on zk.alpha_runs
for each row execute function zk.reject_alpha_aggregation_mutation();

create table zk.alpha_run_contributions (
    alpha_run_id text not null references zk.alpha_runs(alpha_run_id),
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    raw_signal_value numeric not null,
    normalization_rule_id text not null,
    normalized_value numeric not null,
    weight numeric not null,
    weighted_contribution numeric not null,
    created_at timestamptz not null default now(),
    primary key (alpha_run_id, admission_id),
    constraint alpha_run_contributions_text_chk
        check (length(trim(normalization_rule_id)) > 0),
    constraint alpha_run_contributions_finite_chk check (
        raw_signal_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        and normalized_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        and weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        and weighted_contribution not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    )
);

create function zk.validate_alpha_contribution()
returns trigger
language plpgsql
as $$
declare
    run_specification_id text;
    run_definition_version text;
    expected_normalization text;
    expected_weight numeric;
begin
    select r.specification_id, r.definition_version, s.normalization_rule_id
      into run_specification_id, run_definition_version, expected_normalization
      from zk.alpha_runs r
      join zk.alpha_aggregation_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where r.alpha_run_id = new.alpha_run_id;

    select weight into expected_weight
      from zk.alpha_factor_weights
     where specification_id = run_specification_id
       and definition_version = run_definition_version
       and admission_id = new.admission_id;

    if expected_weight is null then
        raise exception 'alpha contribution admission is not in run weight plan';
    end if;
    if new.normalization_rule_id <> expected_normalization then
        raise exception 'alpha contribution normalization does not match specification';
    end if;
    if new.weight <> expected_weight then
        raise exception 'alpha contribution weight does not match specification plan';
    end if;
    if new.weighted_contribution <> new.normalized_value * new.weight then
        raise exception 'alpha contribution arithmetic is inconsistent';
    end if;
    return new;
end;
$$;

create trigger alpha_run_contributions_validate_trg
before insert on zk.alpha_run_contributions
for each row execute function zk.validate_alpha_contribution();

create trigger alpha_run_contributions_immutable_trg
before update or delete on zk.alpha_run_contributions
for each row execute function zk.reject_alpha_aggregation_mutation();

create table zk.alpha_run_unavailable_inputs (
    alpha_run_id text not null references zk.alpha_runs(alpha_run_id),
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    availability_state text not null,
    absolute_weight numeric not null,
    created_at timestamptz not null default now(),
    primary key (alpha_run_id, admission_id),
    constraint alpha_run_unavailable_state_chk
        check (availability_state in ('MISSING', 'NOT_APPLICABLE', 'UNDECIDED')),
    constraint alpha_run_unavailable_weight_chk check (
        absolute_weight > 0
        and absolute_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    )
);

create function zk.validate_alpha_unavailable_input()
returns trigger
language plpgsql
as $$
declare
    run_specification_id text;
    run_definition_version text;
    expected_weight numeric;
begin
    select specification_id, definition_version
      into run_specification_id, run_definition_version
      from zk.alpha_runs
     where alpha_run_id = new.alpha_run_id;

    select abs(weight) into expected_weight
      from zk.alpha_factor_weights
     where specification_id = run_specification_id
       and definition_version = run_definition_version
       and admission_id = new.admission_id;

    if expected_weight is null then
        raise exception 'unavailable alpha admission is not in run weight plan';
    end if;
    if new.absolute_weight <> expected_weight then
        raise exception 'unavailable alpha absolute weight does not match specification plan';
    end if;
    return new;
end;
$$;

create trigger alpha_run_unavailable_inputs_validate_trg
before insert on zk.alpha_run_unavailable_inputs
for each row execute function zk.validate_alpha_unavailable_input();

create trigger alpha_run_unavailable_inputs_immutable_trg
before update or delete on zk.alpha_run_unavailable_inputs
for each row execute function zk.reject_alpha_aggregation_mutation();

create index alpha_runs_security_time_idx
    on zk.alpha_runs(security_id, evaluated_at desc);

create index alpha_factor_admissions_factor_idx
    on zk.alpha_factor_admissions(factor_id, factor_definition_version, horizon_days);
