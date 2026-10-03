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
    planned_factor_count integer not null,
    available_factor_count integer not null,
    planned_absolute_weight numeric not null,
    available_absolute_weight numeric not null,
    created_at timestamptz not null default now(),
    constraint alpha_runs_spec_fk
        foreign key (specification_id, definition_version)
        references zk.alpha_aggregation_specs(specification_id, definition_version),
    constraint alpha_runs_status_chk
        check (status in ('SCORED', 'ABSTAIN_INSUFFICIENT_COVERAGE')),
    constraint alpha_runs_coverage_chk check (coverage >= 0 and coverage <= 1),
    constraint alpha_runs_counts_chk check (
        planned_factor_count > 0
        and available_factor_count >= 0
        and available_factor_count <= planned_factor_count
    ),
    constraint alpha_runs_weights_chk check (
        planned_absolute_weight > 0
        and available_absolute_weight >= 0
        and available_absolute_weight <= planned_absolute_weight
        and planned_absolute_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        and available_absolute_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    ),
    constraint alpha_runs_alpha_finite_chk check (
        alpha_value is null
        or alpha_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    ),
    constraint alpha_runs_score_state_chk check (
        (status = 'SCORED' and alpha_value is not null)
        or (status = 'ABSTAIN_INSUFFICIENT_COVERAGE' and alpha_value is null)
    )
);

create function zk.validate_alpha_run_contract()
returns trigger
language plpgsql
as $
declare
    spec_horizon integer;
    spec_coverage_rule text;
    spec_parameters jsonb;
    expected_field text;
    minimum_coverage numeric;
    expected_planned_weight numeric;
    expected_planned_count integer;
    expected_coverage numeric;
begin
    select horizon_days, coverage_rule_id, parameters
      into spec_horizon, spec_coverage_rule, spec_parameters
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

    if not (spec_parameters ? 'minimum_coverage') then
        raise exception 'aggregation specification requires minimum_coverage';
    end if;
    minimum_coverage := (spec_parameters ->> 'minimum_coverage')::numeric;
    if minimum_coverage < 0 or minimum_coverage > 1 then
        raise exception 'minimum_coverage must be in [0, 1]';
    end if;

    select coalesce(sum(abs(weight)), 0), count(*)
      into expected_planned_weight, expected_planned_count
      from zk.alpha_factor_weights
     where specification_id = new.specification_id
       and definition_version = new.definition_version;

    if expected_planned_count = 0 then
        raise exception 'alpha run requires a non-empty weight plan';
    end if;
    if new.planned_factor_count <> expected_planned_count then
        raise exception 'planned_factor_count does not match specification weight plan';
    end if;
    if new.planned_absolute_weight <> expected_planned_weight then
        raise exception 'planned_absolute_weight does not match specification weight plan';
    end if;

    if spec_coverage_rule = 'ABS_WEIGHT_COVERAGE' then
        expected_coverage := new.available_absolute_weight / new.planned_absolute_weight;
    elsif spec_coverage_rule = 'FACTOR_COUNT_COVERAGE' then
        expected_coverage := new.available_factor_count::numeric / new.planned_factor_count;
    else
        raise exception 'unsupported coverage_rule_id for executable alpha run';
    end if;

    if new.coverage <> expected_coverage then
        raise exception 'alpha run coverage is inconsistent with coverage rule';
    end if;
    if new.status = 'SCORED' and new.coverage < minimum_coverage then
        raise exception 'SCORED alpha run is below minimum coverage';
    end if;
    if new.status = 'ABSTAIN_INSUFFICIENT_COVERAGE'
       and new.coverage >= minimum_coverage then
        raise exception 'ABSTAIN alpha run meets minimum coverage';
    end if;
    return new;
end;
$;

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

create function zk.audit_alpha_run_complete()
returns trigger
language plpgsql
as $
declare
    run_record zk.alpha_runs%rowtype;
    aggregation_rule text;
    contribution_count integer;
    unavailable_count integer;
    contribution_abs_weight numeric;
    contribution_sum numeric;
    expected_alpha numeric;
begin
    select * into run_record
      from zk.alpha_runs
     where alpha_run_id = new.alpha_run_id;

    select aggregation_rule_id into aggregation_rule
      from zk.alpha_aggregation_specs
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    select count(*), coalesce(sum(abs(weight)), 0), coalesce(sum(weighted_contribution), 0)
      into contribution_count, contribution_abs_weight, contribution_sum
      from zk.alpha_run_contributions
     where alpha_run_id = new.alpha_run_id;

    select count(*) into unavailable_count
      from zk.alpha_run_unavailable_inputs
     where alpha_run_id = new.alpha_run_id;

    if exists (
        select 1
        from zk.alpha_run_contributions c
        join zk.alpha_run_unavailable_inputs u
          on u.alpha_run_id = c.alpha_run_id
         and u.admission_id = c.admission_id
        where c.alpha_run_id = new.alpha_run_id
    ) then
        raise exception 'alpha admission cannot be both available and unavailable';
    end if;

    if contribution_count <> run_record.available_factor_count then
        raise exception 'available_factor_count does not match contribution rows';
    end if;
    if contribution_count + unavailable_count <> run_record.planned_factor_count then
        raise exception 'alpha run does not account for every planned factor';
    end if;
    if contribution_abs_weight <> run_record.available_absolute_weight then
        raise exception 'available_absolute_weight does not match contribution rows';
    end if;

    if run_record.status = 'SCORED' then
        if aggregation_rule = 'WEIGHTED_SUM' then
            expected_alpha := contribution_sum;
        elsif aggregation_rule = 'WEIGHTED_ABS_MEAN' then
            if run_record.available_absolute_weight = 0 then
                raise exception 'scored weighted mean cannot have zero available weight';
            end if;
            expected_alpha := contribution_sum / run_record.available_absolute_weight;
        else
            raise exception 'unsupported aggregation_rule_id for executable alpha run';
        end if;
        if run_record.alpha_value <> expected_alpha then
            raise exception 'alpha_value does not match contribution arithmetic';
        end if;
    end if;

    return new;
end;
$;

create constraint trigger alpha_runs_complete_audit_trg
after insert on zk.alpha_runs
deferrable initially deferred
for each row execute function zk.audit_alpha_run_complete();

create index alpha_runs_security_time_idx
    on zk.alpha_runs(security_id, evaluated_at desc);

create index alpha_factor_admissions_factor_idx
    on zk.alpha_factor_admissions(factor_id, factor_definition_version, horizon_days);
