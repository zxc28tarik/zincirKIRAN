-- Zincir Kıran — Regime & Contradiction / Interaction schema v0.1
-- Candidate research context only. No Alpha mutation or portfolio-sizing path.

create table zk.context_research_specs (
    specification_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    base_alpha_specification_id text not null,
    base_alpha_definition_version text not null,
    context_protocol_id text not null,
    universe_rule_version text not null,
    hypothesis text not null,
    success_criteria text not null,
    preregistered_at timestamptz not null,
    stage text not null default 'CANDIDATE',
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint context_research_base_alpha_fk
        foreign key (base_alpha_specification_id, base_alpha_definition_version)
        references zk.alpha_aggregation_specs(specification_id, definition_version),
    constraint context_research_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint context_research_candidate_only_chk
        check (stage = 'CANDIDATE'),
    constraint context_research_text_chk
        check (
            length(trim(specification_id)) > 0
            and length(trim(definition_version)) > 0
            and length(trim(context_protocol_id)) > 0
            and length(trim(universe_rule_version)) > 0
            and length(trim(hypothesis)) > 0
            and length(trim(success_criteria)) > 0
        )
);

create function zk.reject_context_research_mutation()
returns trigger
language plpgsql
as $fn$
begin
    raise exception 'context research records are append-only';
end;
$fn$;

create function zk.validate_context_research_spec()
returns trigger
language plpgsql
as $fn$
declare
    base_horizon integer;
begin
    select horizon_days into base_horizon
      from zk.alpha_aggregation_specs
     where specification_id = new.base_alpha_specification_id
       and definition_version = new.base_alpha_definition_version;

    if base_horizon <> new.horizon_days then
        raise exception 'context research horizon does not match base Alpha';
    end if;
    return new;
end;
$fn$;

create trigger context_research_specs_validate_trg
before insert on zk.context_research_specs
for each row execute function zk.validate_context_research_spec();

create trigger context_research_specs_immutable_trg
before update or delete on zk.context_research_specs
for each row execute function zk.reject_context_research_mutation();

create table zk.context_regime_dimensions (
    specification_id text not null,
    definition_version text not null,
    dimension_id text not null,
    max_age_days integer not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, dimension_id),
    constraint context_regime_dimensions_spec_fk
        foreign key (specification_id, definition_version)
        references zk.context_research_specs(specification_id, definition_version),
    constraint context_regime_dimensions_age_chk
        check (max_age_days >= 0),
    constraint context_regime_dimensions_text_chk
        check (length(trim(dimension_id)) > 0)
);

create trigger context_regime_dimensions_immutable_trg
before update or delete on zk.context_regime_dimensions
for each row execute function zk.reject_context_research_mutation();

create table zk.context_regime_state_rules (
    specification_id text not null,
    definition_version text not null,
    dimension_id text not null,
    state_id text not null,
    lower_inclusive numeric,
    upper_exclusive numeric,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, dimension_id, state_id),
    constraint context_regime_state_dimension_fk
        foreign key (specification_id, definition_version, dimension_id)
        references zk.context_regime_dimensions(
            specification_id, definition_version, dimension_id
        ),
    constraint context_regime_state_bounds_chk
        check (
            lower_inclusive is null
            or upper_exclusive is null
            or lower_inclusive < upper_exclusive
        ),
    constraint context_regime_state_finite_chk
        check (
            (lower_inclusive is null or lower_inclusive not in (
                'NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric
            ))
            and (upper_exclusive is null or upper_exclusive not in (
                'NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric
            ))
        ),
    constraint context_regime_state_text_chk
        check (length(trim(state_id)) > 0)
);

create function zk.validate_context_regime_state_no_overlap()
returns trigger
language plpgsql
as $fn$
begin
    if exists (
        select 1
          from zk.context_regime_state_rules r
         where r.specification_id = new.specification_id
           and r.definition_version = new.definition_version
           and r.dimension_id = new.dimension_id
           and (
               coalesce(new.lower_inclusive, '-Infinity'::numeric)
               < coalesce(r.upper_exclusive, 'Infinity'::numeric)
           )
           and (
               coalesce(r.lower_inclusive, '-Infinity'::numeric)
               < coalesce(new.upper_exclusive, 'Infinity'::numeric)
           )
    ) then
        raise exception 'regime state intervals cannot overlap';
    end if;
    return new;
end;
$fn$;

create trigger context_regime_state_no_overlap_trg
before insert on zk.context_regime_state_rules
for each row execute function zk.validate_context_regime_state_no_overlap();

create trigger context_regime_state_rules_immutable_trg
before update or delete on zk.context_regime_state_rules
for each row execute function zk.reject_context_research_mutation();

create table zk.context_contradiction_rules (
    specification_id text not null,
    definition_version text not null,
    rule_id text not null,
    left_admission_id text not null references zk.alpha_factor_admissions(admission_id),
    right_admission_id text not null references zk.alpha_factor_admissions(admission_id),
    minimum_absolute_signal numeric not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, rule_id),
    constraint context_contradiction_spec_fk
        foreign key (specification_id, definition_version)
        references zk.context_research_specs(specification_id, definition_version),
    constraint context_contradiction_distinct_chk
        check (left_admission_id <> right_admission_id),
    constraint context_contradiction_threshold_chk
        check (
            minimum_absolute_signal >= 0
            and minimum_absolute_signal not in (
                'NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric
            )
        ),
    constraint context_contradiction_text_chk
        check (length(trim(rule_id)) > 0)
);

create table zk.context_interaction_rules (
    specification_id text not null,
    definition_version text not null,
    rule_id text not null,
    left_admission_id text not null references zk.alpha_factor_admissions(admission_id),
    right_admission_id text not null references zk.alpha_factor_admissions(admission_id),
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, rule_id),
    constraint context_interaction_spec_fk
        foreign key (specification_id, definition_version)
        references zk.context_research_specs(specification_id, definition_version),
    constraint context_interaction_distinct_chk
        check (left_admission_id <> right_admission_id),
    constraint context_interaction_text_chk
        check (length(trim(rule_id)) > 0)
);

create function zk.validate_context_rule_admissions()
returns trigger
language plpgsql
as $fn$
declare
    base_spec_id text;
    base_spec_version text;
begin
    select base_alpha_specification_id, base_alpha_definition_version
      into base_spec_id, base_spec_version
      from zk.context_research_specs
     where specification_id = new.specification_id
       and definition_version = new.definition_version;

    if not exists (
        select 1
          from zk.alpha_factor_weights
         where specification_id = base_spec_id
           and definition_version = base_spec_version
           and admission_id = new.left_admission_id
    ) then
        raise exception 'left context rule admission is outside base Alpha plan';
    end if;

    if not exists (
        select 1
          from zk.alpha_factor_weights
         where specification_id = base_spec_id
           and definition_version = base_spec_version
           and admission_id = new.right_admission_id
    ) then
        raise exception 'right context rule admission is outside base Alpha plan';
    end if;
    return new;
end;
$fn$;

create trigger context_contradiction_rule_admission_trg
before insert on zk.context_contradiction_rules
for each row execute function zk.validate_context_rule_admissions();

create trigger context_interaction_rule_admission_trg
before insert on zk.context_interaction_rules
for each row execute function zk.validate_context_rule_admissions();

create trigger context_contradiction_rules_immutable_trg
before update or delete on zk.context_contradiction_rules
for each row execute function zk.reject_context_research_mutation();

create trigger context_interaction_rules_immutable_trg
before update or delete on zk.context_interaction_rules
for each row execute function zk.reject_context_research_mutation();

create table zk.context_contradiction_regime_requirements (
    specification_id text not null,
    definition_version text not null,
    rule_id text not null,
    dimension_id text not null,
    state_id text not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, rule_id, dimension_id),
    constraint context_contradiction_requirement_rule_fk
        foreign key (specification_id, definition_version, rule_id)
        references zk.context_contradiction_rules(
            specification_id, definition_version, rule_id
        ),
    constraint context_contradiction_requirement_state_fk
        foreign key (specification_id, definition_version, dimension_id, state_id)
        references zk.context_regime_state_rules(
            specification_id, definition_version, dimension_id, state_id
        )
);

create table zk.context_interaction_regime_requirements (
    specification_id text not null,
    definition_version text not null,
    rule_id text not null,
    dimension_id text not null,
    state_id text not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, rule_id, dimension_id),
    constraint context_interaction_requirement_rule_fk
        foreign key (specification_id, definition_version, rule_id)
        references zk.context_interaction_rules(
            specification_id, definition_version, rule_id
        ),
    constraint context_interaction_requirement_state_fk
        foreign key (specification_id, definition_version, dimension_id, state_id)
        references zk.context_regime_state_rules(
            specification_id, definition_version, dimension_id, state_id
        )
);

create trigger context_contradiction_requirements_immutable_trg
before update or delete on zk.context_contradiction_regime_requirements
for each row execute function zk.reject_context_research_mutation();

create trigger context_interaction_requirements_immutable_trg
before update or delete on zk.context_interaction_regime_requirements
for each row execute function zk.reject_context_research_mutation();

create table zk.context_regime_observations (
    observation_id text primary key,
    dimension_id text not null,
    context_protocol_id text not null,
    raw_value numeric not null,
    window_start timestamptz not null,
    window_end timestamptz not null,
    available_at timestamptz not null,
    source_snapshot_id text not null,
    created_at timestamptz not null default now(),
    constraint context_regime_observation_time_chk
        check (window_start <= window_end and window_end <= available_at),
    constraint context_regime_observation_value_chk
        check (
            raw_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint context_regime_observation_text_chk
        check (
            length(trim(observation_id)) > 0
            and length(trim(dimension_id)) > 0
            and length(trim(context_protocol_id)) > 0
            and length(trim(source_snapshot_id)) > 0
        )
);

create trigger context_regime_observations_immutable_trg
before update or delete on zk.context_regime_observations
for each row execute function zk.reject_context_research_mutation();

create table zk.context_runs (
    context_run_id text primary key,
    specification_id text not null,
    definition_version text not null,
    prediction_timestamp timestamptz not null,
    status text not null,
    created_at timestamptz not null default now(),
    constraint context_runs_spec_fk
        foreign key (specification_id, definition_version)
        references zk.context_research_specs(specification_id, definition_version),
    constraint context_runs_status_chk
        check (status in (
            'EVALUATED',
            'ABSTAIN_INSUFFICIENT_REGIME',
            'ABSTAIN_INSUFFICIENT_FACTOR_SIGNALS'
        )),
    constraint context_runs_text_chk
        check (length(trim(context_run_id)) > 0)
);

create function zk.validate_context_run()
returns trigger
language plpgsql
as $fn$
declare
    preregistered_time timestamptz;
begin
    select preregistered_at into preregistered_time
      from zk.context_research_specs
     where specification_id = new.specification_id
       and definition_version = new.definition_version;

    if preregistered_time > new.prediction_timestamp then
        raise exception 'context research protocol was not preregistered by prediction time';
    end if;
    return new;
end;
$fn$;

create trigger context_runs_validate_trg
before insert on zk.context_runs
for each row execute function zk.validate_context_run();

create trigger context_runs_immutable_trg
before update or delete on zk.context_runs
for each row execute function zk.reject_context_research_mutation();

create table zk.context_factor_signals (
    context_run_id text not null references zk.context_runs(context_run_id),
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    normalized_signal_value numeric not null,
    created_at timestamptz not null default now(),
    primary key (context_run_id, admission_id),
    constraint context_factor_signal_finite_chk
        check (
            normalized_signal_value not in (
                'NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric
            )
        )
);

create function zk.validate_context_factor_signal()
returns trigger
language plpgsql
as $fn$
declare
    base_spec_id text;
    base_spec_version text;
begin
    select s.base_alpha_specification_id, s.base_alpha_definition_version
      into base_spec_id, base_spec_version
      from zk.context_runs r
      join zk.context_research_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where r.context_run_id = new.context_run_id;

    if not exists (
        select 1
          from zk.alpha_factor_weights
         where specification_id = base_spec_id
           and definition_version = base_spec_version
           and admission_id = new.admission_id
    ) then
        raise exception 'context factor signal is outside base Alpha plan';
    end if;
    return new;
end;
$fn$;

create trigger context_factor_signals_validate_trg
before insert on zk.context_factor_signals
for each row execute function zk.validate_context_factor_signal();

create trigger context_factor_signals_immutable_trg
before update or delete on zk.context_factor_signals
for each row execute function zk.reject_context_research_mutation();

create table zk.context_regime_results (
    context_run_id text not null references zk.context_runs(context_run_id),
    dimension_id text not null,
    availability text not null,
    observation_id text references zk.context_regime_observations(observation_id),
    state_id text,
    created_at timestamptz not null default now(),
    primary key (context_run_id, dimension_id),
    constraint context_regime_result_availability_chk
        check (availability in ('CLASSIFIED', 'MISSING', 'STALE')),
    constraint context_regime_result_shape_chk
        check (
            (availability = 'CLASSIFIED' and observation_id is not null and state_id is not null)
            or (availability = 'STALE' and observation_id is not null and state_id is null)
            or (availability = 'MISSING' and observation_id is null and state_id is null)
        )
);

create function zk.validate_context_regime_result()
returns trigger
language plpgsql
as $fn$
declare
    spec_id text;
    spec_version text;
    protocol_id text;
    prediction_time timestamptz;
    max_age integer;
    obs_dimension text;
    obs_protocol text;
    obs_raw numeric;
    obs_window_end timestamptz;
    obs_available_at timestamptz;
    age_days numeric;
    lower_bound numeric;
    upper_bound numeric;
begin
    select r.specification_id, r.definition_version, s.context_protocol_id,
           r.prediction_timestamp
      into spec_id, spec_version, protocol_id, prediction_time
      from zk.context_runs r
      join zk.context_research_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where r.context_run_id = new.context_run_id;

    select max_age_days into max_age
      from zk.context_regime_dimensions
     where specification_id = spec_id
       and definition_version = spec_version
       and dimension_id = new.dimension_id;

    if max_age is null then
        raise exception 'context regime dimension is not declared in specification';
    end if;

    if new.availability = 'MISSING' then
        return new;
    end if;

    select dimension_id, context_protocol_id, raw_value, window_end, available_at
      into obs_dimension, obs_protocol, obs_raw, obs_window_end, obs_available_at
      from zk.context_regime_observations
     where observation_id = new.observation_id;

    if obs_dimension <> new.dimension_id then
        raise exception 'regime result observation dimension mismatch';
    end if;
    if obs_protocol <> protocol_id then
        raise exception 'regime result observation protocol mismatch';
    end if;
    if obs_window_end > prediction_time or obs_available_at > prediction_time then
        raise exception 'future regime evidence cannot enter context run';
    end if;

    age_days := extract(epoch from (prediction_time - obs_window_end)) / 86400;

    if new.availability = 'STALE' then
        if age_days <= max_age then
            raise exception 'STALE regime result requires evidence older than max age';
        end if;
        return new;
    end if;

    if age_days > max_age then
        raise exception 'stale regime evidence cannot be CLASSIFIED';
    end if;

    select lower_inclusive, upper_exclusive
      into lower_bound, upper_bound
      from zk.context_regime_state_rules
     where specification_id = spec_id
       and definition_version = spec_version
       and dimension_id = new.dimension_id
       and state_id = new.state_id;

    if not found then
        raise exception 'classified regime state is not declared';
    end if;
    if lower_bound is not null and obs_raw < lower_bound then
        raise exception 'regime observation does not satisfy state lower bound';
    end if;
    if upper_bound is not null and obs_raw >= upper_bound then
        raise exception 'regime observation does not satisfy state upper bound';
    end if;
    return new;
end;
$fn$;

create trigger context_regime_results_validate_trg
before insert on zk.context_regime_results
for each row execute function zk.validate_context_regime_result();

create trigger context_regime_results_immutable_trg
before update or delete on zk.context_regime_results
for each row execute function zk.reject_context_research_mutation();

create table zk.context_missing_factor_signals (
    context_run_id text not null references zk.context_runs(context_run_id),
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    created_at timestamptz not null default now(),
    primary key (context_run_id, admission_id)
);

create trigger context_missing_factor_signals_immutable_trg
before update or delete on zk.context_missing_factor_signals
for each row execute function zk.reject_context_research_mutation();

create table zk.context_contradiction_results (
    context_run_id text not null references zk.context_runs(context_run_id),
    rule_id text not null,
    left_signal numeric not null,
    right_signal numeric not null,
    regime_condition_met boolean not null,
    is_contradiction boolean not null,
    created_at timestamptz not null default now(),
    primary key (context_run_id, rule_id),
    constraint context_contradiction_result_finite_chk
        check (
            left_signal not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and right_signal not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        )
);

create function zk.validate_context_contradiction_result()
returns trigger
language plpgsql
as $fn$
declare
    spec_id text;
    spec_version text;
    left_admission text;
    right_admission text;
    threshold numeric;
    expected_left numeric;
    expected_right numeric;
    expected_regime boolean;
    expected_contradiction boolean;
begin
    select specification_id, definition_version
      into spec_id, spec_version
      from zk.context_runs
     where context_run_id = new.context_run_id;

    select left_admission_id, right_admission_id, minimum_absolute_signal
      into left_admission, right_admission, threshold
      from zk.context_contradiction_rules
     where specification_id = spec_id
       and definition_version = spec_version
       and rule_id = new.rule_id;

    if left_admission is null then
        raise exception 'contradiction result rule is not declared';
    end if;

    select normalized_signal_value into expected_left
      from zk.context_factor_signals
     where context_run_id = new.context_run_id
       and admission_id = left_admission;
    select normalized_signal_value into expected_right
      from zk.context_factor_signals
     where context_run_id = new.context_run_id
       and admission_id = right_admission;

    if expected_left is null or expected_right is null then
        raise exception 'contradiction result requires both factor signals';
    end if;

    expected_regime := not exists (
        select 1
          from zk.context_contradiction_regime_requirements q
         where q.specification_id = spec_id
           and q.definition_version = spec_version
           and q.rule_id = new.rule_id
           and not exists (
               select 1
                 from zk.context_regime_results rr
                where rr.context_run_id = new.context_run_id
                  and rr.dimension_id = q.dimension_id
                  and rr.availability = 'CLASSIFIED'
                  and rr.state_id = q.state_id
           )
    );

    expected_contradiction := (
        expected_regime
        and abs(expected_left) >= threshold
        and abs(expected_right) >= threshold
        and expected_left * expected_right < 0
    );

    if new.left_signal <> expected_left or new.right_signal <> expected_right then
        raise exception 'contradiction result signal values mismatch';
    end if;
    if new.regime_condition_met <> expected_regime then
        raise exception 'contradiction regime condition mismatch';
    end if;
    if new.is_contradiction <> expected_contradiction then
        raise exception 'contradiction arithmetic mismatch';
    end if;
    return new;
end;
$fn$;

create trigger context_contradiction_results_validate_trg
before insert on zk.context_contradiction_results
for each row execute function zk.validate_context_contradiction_result();

create trigger context_contradiction_results_immutable_trg
before update or delete on zk.context_contradiction_results
for each row execute function zk.reject_context_research_mutation();

create table zk.context_interaction_results (
    context_run_id text not null references zk.context_runs(context_run_id),
    rule_id text not null,
    left_signal numeric not null,
    right_signal numeric not null,
    state text not null,
    interaction_value numeric,
    created_at timestamptz not null default now(),
    primary key (context_run_id, rule_id),
    constraint context_interaction_result_state_chk
        check (state in ('ACTIVE', 'INACTIVE_REGIME')),
    constraint context_interaction_result_shape_chk
        check (
            (state = 'ACTIVE' and interaction_value is not null)
            or (state = 'INACTIVE_REGIME' and interaction_value is null)
        ),
    constraint context_interaction_result_finite_chk
        check (
            left_signal not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and right_signal not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and (
                interaction_value is null
                or interaction_value not in (
                    'NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric
                )
            )
        )
);

create function zk.validate_context_interaction_result()
returns trigger
language plpgsql
as $fn$
declare
    spec_id text;
    spec_version text;
    left_admission text;
    right_admission text;
    expected_left numeric;
    expected_right numeric;
    expected_regime boolean;
    expected_state text;
    expected_value numeric;
begin
    select specification_id, definition_version
      into spec_id, spec_version
      from zk.context_runs
     where context_run_id = new.context_run_id;

    select left_admission_id, right_admission_id
      into left_admission, right_admission
      from zk.context_interaction_rules
     where specification_id = spec_id
       and definition_version = spec_version
       and rule_id = new.rule_id;

    if left_admission is null then
        raise exception 'interaction result rule is not declared';
    end if;

    select normalized_signal_value into expected_left
      from zk.context_factor_signals
     where context_run_id = new.context_run_id
       and admission_id = left_admission;
    select normalized_signal_value into expected_right
      from zk.context_factor_signals
     where context_run_id = new.context_run_id
       and admission_id = right_admission;

    if expected_left is null or expected_right is null then
        raise exception 'interaction result requires both factor signals';
    end if;

    expected_regime := not exists (
        select 1
          from zk.context_interaction_regime_requirements q
         where q.specification_id = spec_id
           and q.definition_version = spec_version
           and q.rule_id = new.rule_id
           and not exists (
               select 1
                 from zk.context_regime_results rr
                where rr.context_run_id = new.context_run_id
                  and rr.dimension_id = q.dimension_id
                  and rr.availability = 'CLASSIFIED'
                  and rr.state_id = q.state_id
           )
    );

    expected_state := case when expected_regime then 'ACTIVE' else 'INACTIVE_REGIME' end;
    expected_value := case when expected_regime then expected_left * expected_right else null end;

    if new.left_signal <> expected_left or new.right_signal <> expected_right then
        raise exception 'interaction result signal values mismatch';
    end if;
    if new.state <> expected_state then
        raise exception 'interaction regime state mismatch';
    end if;
    if (
        (expected_value is null and new.interaction_value is not null)
        or (expected_value is not null and new.interaction_value <> expected_value)
    ) then
        raise exception 'interaction arithmetic mismatch';
    end if;
    return new;
end;
$fn$;

create trigger context_interaction_results_validate_trg
before insert on zk.context_interaction_results
for each row execute function zk.validate_context_interaction_result();

create trigger context_interaction_results_immutable_trg
before update or delete on zk.context_interaction_results
for each row execute function zk.reject_context_research_mutation();

create function zk.audit_context_run_complete()
returns trigger
language plpgsql
as $fn$
declare
    run_record zk.context_runs%rowtype;
    spec_record zk.context_research_specs%rowtype;
    dimension_count integer;
    regime_result_count integer;
    classified_count integer;
    unavailable_regime_count integer;
    contradiction_rule_count integer;
    interaction_rule_count integer;
    contradiction_result_count integer;
    interaction_result_count integer;
    missing_signal_count integer;
    required_signal_count integer;
    present_required_signal_count integer;
begin
    select * into run_record
      from zk.context_runs
     where context_run_id = new.context_run_id;

    select * into spec_record
      from zk.context_research_specs
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    select count(*) into dimension_count
      from zk.context_regime_dimensions
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    if dimension_count = 0 then
        raise exception 'context research specification requires regime dimensions';
    end if;

    select count(*),
           count(*) filter (where availability = 'CLASSIFIED'),
           count(*) filter (where availability <> 'CLASSIFIED')
      into regime_result_count, classified_count, unavailable_regime_count
      from zk.context_regime_results
     where context_run_id = new.context_run_id;

    if regime_result_count <> dimension_count then
        raise exception 'context run must account for every regime dimension';
    end if;

    select count(*) into contradiction_rule_count
      from zk.context_contradiction_rules
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    select count(*) into interaction_rule_count
      from zk.context_interaction_rules
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    select count(*) into contradiction_result_count
      from zk.context_contradiction_results
     where context_run_id = new.context_run_id;
    select count(*) into interaction_result_count
      from zk.context_interaction_results
     where context_run_id = new.context_run_id;
    select count(*) into missing_signal_count
      from zk.context_missing_factor_signals
     where context_run_id = new.context_run_id;

    with required as (
        select left_admission_id as admission_id
          from zk.context_contradiction_rules
         where specification_id = run_record.specification_id
           and definition_version = run_record.definition_version
        union
        select right_admission_id
          from zk.context_contradiction_rules
         where specification_id = run_record.specification_id
           and definition_version = run_record.definition_version
        union
        select left_admission_id
          from zk.context_interaction_rules
         where specification_id = run_record.specification_id
           and definition_version = run_record.definition_version
        union
        select right_admission_id
          from zk.context_interaction_rules
         where specification_id = run_record.specification_id
           and definition_version = run_record.definition_version
    )
    select count(*),
           count(*) filter (
               where exists (
                   select 1
                     from zk.context_factor_signals fs
                    where fs.context_run_id = run_record.context_run_id
                      and fs.admission_id = required.admission_id
               )
           )
      into required_signal_count, present_required_signal_count
      from required;

    if run_record.status = 'EVALUATED' then
        if unavailable_regime_count <> 0 or classified_count <> dimension_count then
            raise exception 'evaluated context run requires all regimes classified';
        end if;
        if present_required_signal_count <> required_signal_count then
            raise exception 'evaluated context run requires all rule factor signals';
        end if;
        if missing_signal_count <> 0 then
            raise exception 'evaluated context run cannot contain missing factor signals';
        end if;
        if contradiction_result_count <> contradiction_rule_count then
            raise exception 'evaluated context run requires every contradiction result';
        end if;
        if interaction_result_count <> interaction_rule_count then
            raise exception 'evaluated context run requires every interaction result';
        end if;
    elsif run_record.status = 'ABSTAIN_INSUFFICIENT_REGIME' then
        if unavailable_regime_count = 0 then
            raise exception 'regime-abstained context run requires missing/stale regime evidence';
        end if;
        if contradiction_result_count <> 0 or interaction_result_count <> 0 then
            raise exception 'regime-abstained context run cannot emit rule results';
        end if;
    else
        if unavailable_regime_count <> 0 then
            raise exception 'factor-signal abstention requires all regimes classified';
        end if;
        if missing_signal_count = 0 then
            raise exception 'factor-signal abstention requires missing rule signals';
        end if;
        if contradiction_result_count <> 0 or interaction_result_count <> 0 then
            raise exception 'factor-signal-abstained run cannot emit rule results';
        end if;
        if exists (
            select 1
              from zk.context_missing_factor_signals ms
             where ms.context_run_id = run_record.context_run_id
               and not exists (
                   select 1
                     from (
                         select left_admission_id as admission_id
                           from zk.context_contradiction_rules
                          where specification_id = run_record.specification_id
                            and definition_version = run_record.definition_version
                         union
                         select right_admission_id
                           from zk.context_contradiction_rules
                          where specification_id = run_record.specification_id
                            and definition_version = run_record.definition_version
                         union
                         select left_admission_id
                           from zk.context_interaction_rules
                          where specification_id = run_record.specification_id
                            and definition_version = run_record.definition_version
                         union
                         select right_admission_id
                           from zk.context_interaction_rules
                          where specification_id = run_record.specification_id
                            and definition_version = run_record.definition_version
                     ) required
                    where required.admission_id = ms.admission_id
               )
        ) then
            raise exception 'missing context signal is not required by any rule';
        end if;
    end if;

    return new;
end;
$fn$;

create constraint trigger context_runs_complete_audit_trg
after insert on zk.context_runs
deferrable initially deferred
for each row execute function zk.audit_context_run_complete();

create index context_regime_observations_dimension_time_idx
    on zk.context_regime_observations(dimension_id, available_at desc);

create index context_runs_prediction_idx
    on zk.context_runs(prediction_timestamp desc);
