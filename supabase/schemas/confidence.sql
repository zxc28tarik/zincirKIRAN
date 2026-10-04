-- Zincir Kıran — Confidence / Abstain schema v0.1
-- Confidence is separate from Alpha and cannot mutate Alpha or portfolio sizing.

create table zk.confidence_specs (
    specification_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    base_alpha_specification_id text not null,
    base_alpha_definition_version text not null,
    confidence_protocol_id text not null,
    universe_rule_version text not null,
    hypothesis text not null,
    success_criteria text not null,
    preregistered_at timestamptz not null,
    minimum_weight_coverage numeric not null,
    signal_eligibility_threshold numeric not null,
    stage text not null default 'CANDIDATE',
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint confidence_specs_base_alpha_fk
        foreign key (base_alpha_specification_id, base_alpha_definition_version)
        references zk.alpha_aggregation_specs(specification_id, definition_version),
    constraint confidence_specs_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint confidence_specs_coverage_chk
        check (minimum_weight_coverage > 0 and minimum_weight_coverage <= 1),
    constraint confidence_specs_threshold_chk
        check (signal_eligibility_threshold >= 0 and signal_eligibility_threshold <= 1),
    constraint confidence_specs_candidate_only_chk
        check (stage = 'CANDIDATE'),
    constraint confidence_specs_text_chk
        check (
            length(trim(specification_id)) > 0
            and length(trim(definition_version)) > 0
            and length(trim(confidence_protocol_id)) > 0
            and length(trim(universe_rule_version)) > 0
            and length(trim(hypothesis)) > 0
            and length(trim(success_criteria)) > 0
        )
);

create function zk.reject_confidence_mutation()
returns trigger
language plpgsql
as $fn$
begin
    raise exception 'confidence records are append-only';
end;
$fn$;

create function zk.validate_confidence_spec()
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
        raise exception 'confidence horizon does not match base Alpha';
    end if;
    return new;
end;
$fn$;

create trigger confidence_specs_validate_trg
before insert on zk.confidence_specs
for each row execute function zk.validate_confidence_spec();

create trigger confidence_specs_immutable_trg
before update or delete on zk.confidence_specs
for each row execute function zk.reject_confidence_mutation();

create table zk.confidence_dimensions (
    specification_id text not null,
    definition_version text not null,
    dimension_id text not null,
    kind text not null,
    required boolean not null,
    max_age_days integer not null,
    weight numeric not null,
    bad_reference numeric not null,
    good_reference numeric not null,
    hard_floor numeric,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, dimension_id),
    constraint confidence_dimensions_spec_fk
        foreign key (specification_id, definition_version)
        references zk.confidence_specs(specification_id, definition_version),
    constraint confidence_dimensions_kind_chk
        check (kind in (
            'DATA_COVERAGE', 'FRESHNESS', 'PIT_CERTAINTY',
            'FACTOR_EVIDENCE', 'LIQUIDITY', 'MODEL_AGREEMENT'
        )),
    constraint confidence_dimensions_age_chk
        check (max_age_days >= 0),
    constraint confidence_dimensions_weight_chk
        check (
            weight > 0
            and weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint confidence_dimensions_reference_chk
        check (
            bad_reference <> good_reference
            and bad_reference not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and good_reference not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint confidence_dimensions_floor_chk
        check (hard_floor is null or (hard_floor >= 0 and hard_floor <= 1)),
    constraint confidence_dimensions_text_chk
        check (length(trim(dimension_id)) > 0)
);

create trigger confidence_dimensions_immutable_trg
before update or delete on zk.confidence_dimensions
for each row execute function zk.reject_confidence_mutation();

create table zk.confidence_observations (
    observation_id text primary key,
    security_id uuid not null references zk.securities(security_id),
    dimension_id text not null,
    confidence_protocol_id text not null,
    raw_value numeric not null,
    window_start timestamptz not null,
    window_end timestamptz not null,
    available_at timestamptz not null,
    source_reference text not null,
    created_at timestamptz not null default now(),
    constraint confidence_observation_time_chk
        check (window_start <= window_end and window_end <= available_at),
    constraint confidence_observation_value_chk
        check (
            raw_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint confidence_observation_text_chk
        check (
            length(trim(observation_id)) > 0
            and length(trim(dimension_id)) > 0
            and length(trim(confidence_protocol_id)) > 0
            and length(trim(source_reference)) > 0
        )
);

create trigger confidence_observations_immutable_trg
before update or delete on zk.confidence_observations
for each row execute function zk.reject_confidence_mutation();

create table zk.confidence_runs (
    confidence_run_id text primary key,
    specification_id text not null,
    definition_version text not null,
    alpha_run_id text not null references zk.alpha_runs(alpha_run_id),
    prediction_timestamp timestamptz not null,
    source_alpha_value numeric,
    decision text not null,
    confidence_score numeric,
    evidence_weight_coverage numeric not null,
    available_weight numeric not null,
    total_weight numeric not null,
    created_at timestamptz not null default now(),
    constraint confidence_runs_spec_fk
        foreign key (specification_id, definition_version)
        references zk.confidence_specs(specification_id, definition_version),
    constraint confidence_runs_decision_chk
        check (decision in (
            'SIGNAL_ELIGIBLE',
            'NO_SIGNAL_ALPHA_UNAVAILABLE',
            'NO_SIGNAL_REQUIRED_EVIDENCE',
            'NO_SIGNAL_INSUFFICIENT_COVERAGE',
            'NO_SIGNAL_HARD_FLOOR',
            'NO_SIGNAL_LOW_CONFIDENCE'
        )),
    constraint confidence_runs_coverage_chk
        check (evidence_weight_coverage >= 0 and evidence_weight_coverage <= 1),
    constraint confidence_runs_weight_chk
        check (
            total_weight > 0
            and available_weight >= 0
            and available_weight <= total_weight
            and total_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and available_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint confidence_runs_score_chk
        check (
            confidence_score is null
            or (
                confidence_score >= 0
                and confidence_score <= 1
                and confidence_score not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            )
        ),
    constraint confidence_runs_alpha_value_chk
        check (
            source_alpha_value is null
            or source_alpha_value not in (
                'NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric
            )
        )
);

create function zk.validate_confidence_run()
returns trigger
language plpgsql
as $fn$
declare
    preregistered_time timestamptz;
    base_spec_id text;
    base_spec_version text;
    alpha_spec_id text;
    alpha_spec_version text;
    alpha_status text;
    source_alpha_db_value numeric;
begin
    select preregistered_at, base_alpha_specification_id, base_alpha_definition_version
      into preregistered_time, base_spec_id, base_spec_version
      from zk.confidence_specs
     where specification_id = new.specification_id
       and definition_version = new.definition_version;

    if preregistered_time > new.prediction_timestamp then
        raise exception 'confidence protocol was not preregistered by prediction time';
    end if;

    select a.specification_id, a.definition_version, a.status, a.alpha_value
      into alpha_spec_id, alpha_spec_version, alpha_status, source_alpha_db_value
      from zk.alpha_runs a
     where a.alpha_run_id = new.alpha_run_id;

    if alpha_spec_id <> base_spec_id or alpha_spec_version <> base_spec_version then
        raise exception 'confidence run references a different base Alpha';
    end if;

    if alpha_status = 'SCORED' then
        if (
            source_alpha_db_value is null
            or new.source_alpha_value is null
            or new.source_alpha_value <> source_alpha_db_value
        ) then
            raise exception 'confidence source_alpha_value must equal scored Alpha';
        end if;
    else
        if source_alpha_db_value is not null or new.source_alpha_value is not null then
            raise exception 'abstained Alpha cannot carry confidence source_alpha_value';
        end if;
    end if;

    return new;
end;
$fn$;

create trigger confidence_runs_validate_trg
before insert on zk.confidence_runs
for each row execute function zk.validate_confidence_run();

create trigger confidence_runs_immutable_trg
before update or delete on zk.confidence_runs
for each row execute function zk.reject_confidence_mutation();

create table zk.confidence_dimension_results (
    confidence_run_id text not null references zk.confidence_runs(confidence_run_id),
    dimension_id text not null,
    availability text not null,
    observation_id text references zk.confidence_observations(observation_id),
    raw_value numeric,
    normalized_quality numeric,
    weight numeric not null,
    weighted_contribution numeric,
    hard_floor numeric,
    hard_floor_pass boolean,
    age_days numeric,
    created_at timestamptz not null default now(),
    primary key (confidence_run_id, dimension_id),
    constraint confidence_dimension_results_availability_chk
        check (availability in ('AVAILABLE', 'MISSING', 'STALE')),
    constraint confidence_dimension_results_quality_chk
        check (
            normalized_quality is null
            or (normalized_quality >= 0 and normalized_quality <= 1)
        ),
    constraint confidence_dimension_results_weight_chk
        check (weight > 0),
    constraint confidence_dimension_results_shape_chk
        check (
            (
                availability = 'AVAILABLE'
                and observation_id is not null
                and raw_value is not null
                and normalized_quality is not null
                and weighted_contribution is not null
                and age_days is not null
            )
            or (
                availability = 'STALE'
                and observation_id is not null
                and raw_value is not null
                and normalized_quality is null
                and weighted_contribution is null
                and hard_floor_pass is null
                and age_days is not null
            )
            or (
                availability = 'MISSING'
                and observation_id is null
                and raw_value is null
                and normalized_quality is null
                and weighted_contribution is null
                and hard_floor_pass is null
                and age_days is null
            )
        )
);

create function zk.validate_confidence_dimension_result()
returns trigger
language plpgsql
as $fn$
declare
    spec_id text;
    spec_version text;
    protocol_id text;
    prediction_time timestamptz;
    alpha_security uuid;
    required_flag boolean;
    max_age integer;
    expected_weight numeric;
    bad_ref numeric;
    good_ref numeric;
    expected_floor numeric;
    obs_security uuid;
    obs_dimension text;
    obs_protocol text;
    obs_raw numeric;
    obs_window_end timestamptz;
    obs_available_at timestamptz;
    expected_age numeric;
    expected_quality numeric;
    expected_floor_pass boolean;
begin
    select r.specification_id, r.definition_version, s.confidence_protocol_id,
           r.prediction_timestamp, a.security_id
      into spec_id, spec_version, protocol_id, prediction_time, alpha_security
      from zk.confidence_runs r
      join zk.confidence_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
      join zk.alpha_runs a on a.alpha_run_id = r.alpha_run_id
     where r.confidence_run_id = new.confidence_run_id;

    select required, max_age_days, weight, bad_reference, good_reference, hard_floor
      into required_flag, max_age, expected_weight, bad_ref, good_ref, expected_floor
      from zk.confidence_dimensions
     where specification_id = spec_id
       and definition_version = spec_version
       and dimension_id = new.dimension_id;

    if not found then
        raise exception 'confidence dimension is not declared in specification';
    end if;
    if new.weight <> expected_weight then
        raise exception 'confidence dimension result weight mismatch';
    end if;
    if new.hard_floor is distinct from expected_floor then
        raise exception 'confidence dimension result hard_floor mismatch';
    end if;

    if new.availability = 'MISSING' then
        return new;
    end if;

    select security_id, dimension_id, confidence_protocol_id, raw_value,
           window_end, available_at
      into obs_security, obs_dimension, obs_protocol, obs_raw,
           obs_window_end, obs_available_at
      from zk.confidence_observations
     where observation_id = new.observation_id;

    if obs_security <> alpha_security then
        raise exception 'confidence observation security mismatch';
    end if;
    if obs_dimension <> new.dimension_id then
        raise exception 'confidence observation dimension mismatch';
    end if;
    if obs_protocol <> protocol_id then
        raise exception 'confidence observation protocol mismatch';
    end if;
    if obs_window_end > prediction_time or obs_available_at > prediction_time then
        raise exception 'future confidence evidence cannot enter confidence run';
    end if;

    expected_age := extract(epoch from (prediction_time - obs_window_end)) / 86400;

    if new.availability = 'STALE' then
        if expected_age <= max_age then
            raise exception 'STALE confidence result requires evidence older than max age';
        end if;
        if new.raw_value <> obs_raw or new.age_days <> expected_age then
            raise exception 'stale confidence result provenance mismatch';
        end if;
        return new;
    end if;

    if expected_age > max_age then
        raise exception 'stale confidence evidence cannot be AVAILABLE';
    end if;

    expected_quality := least(
        1::numeric,
        greatest(0::numeric, (obs_raw - bad_ref) / (good_ref - bad_ref))
    );
    expected_floor_pass := case
        when expected_floor is null then null
        else expected_quality >= expected_floor
    end;

    if new.raw_value <> obs_raw then
        raise exception 'confidence result raw_value mismatch';
    end if;
    if new.age_days <> expected_age then
        raise exception 'confidence result age mismatch';
    end if;
    if new.normalized_quality <> expected_quality then
        raise exception 'confidence normalization arithmetic mismatch';
    end if;
    if new.weighted_contribution <> expected_quality * expected_weight then
        raise exception 'confidence weighted contribution mismatch';
    end if;
    if new.hard_floor_pass is distinct from expected_floor_pass then
        raise exception 'confidence hard-floor result mismatch';
    end if;
    return new;
end;
$fn$;

create trigger confidence_dimension_results_validate_trg
before insert on zk.confidence_dimension_results
for each row execute function zk.validate_confidence_dimension_result();

create trigger confidence_dimension_results_immutable_trg
before update or delete on zk.confidence_dimension_results
for each row execute function zk.reject_confidence_mutation();

create table zk.confidence_abstention_reasons (
    confidence_reason_id bigint generated always as identity primary key,
    confidence_run_id text not null references zk.confidence_runs(confidence_run_id),
    reason_code text not null,
    dimension_id text,
    created_at timestamptz not null default now(),
    constraint confidence_reason_code_chk
        check (reason_code in (
            'ALPHA_UNAVAILABLE',
            'REQUIRED_EVIDENCE',
            'INSUFFICIENT_CONFIDENCE_COVERAGE',
            'HARD_FLOOR',
            'LOW_CONFIDENCE_SCORE'
        )),
    constraint confidence_reason_shape_chk
        check (
            (reason_code in ('REQUIRED_EVIDENCE', 'HARD_FLOOR') and dimension_id is not null)
            or (reason_code not in ('REQUIRED_EVIDENCE', 'HARD_FLOOR') and dimension_id is null)
        )
);

create unique index confidence_abstention_reason_identity_uidx
    on zk.confidence_abstention_reasons(
        confidence_run_id,
        reason_code,
        coalesce(dimension_id, '')
    );

create trigger confidence_abstention_reasons_immutable_trg
before update or delete on zk.confidence_abstention_reasons
for each row execute function zk.reject_confidence_mutation();

create function zk.audit_confidence_run_complete()
returns trigger
language plpgsql
as $fn$
declare
    run_record zk.confidence_runs%rowtype;
    spec_record zk.confidence_specs%rowtype;
    alpha_status text;
    dimension_count integer;
    result_count integer;
    total_weight_expected numeric;
    available_weight_expected numeric;
    coverage_expected numeric;
    required_unavailable_count integer;
    hard_floor_failure_count integer;
    score_expected numeric;
    decision_expected text;
    reason_count integer;
    expected_reason_count integer;
begin
    select * into run_record
      from zk.confidence_runs
     where confidence_run_id = new.confidence_run_id;

    select * into spec_record
      from zk.confidence_specs
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    select status into alpha_status
      from zk.alpha_runs
     where alpha_run_id = run_record.alpha_run_id;

    select count(*), sum(weight)
      into dimension_count, total_weight_expected
      from zk.confidence_dimensions
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    if dimension_count = 0 then
        raise exception 'confidence specification requires dimensions';
    end if;

    select count(*),
           coalesce(sum(weight) filter (where availability = 'AVAILABLE'), 0)
      into result_count, available_weight_expected
      from zk.confidence_dimension_results
     where confidence_run_id = run_record.confidence_run_id;

    if result_count <> dimension_count then
        raise exception 'confidence run must account for every dimension';
    end if;

    coverage_expected := available_weight_expected / total_weight_expected;

    if run_record.total_weight <> total_weight_expected then
        raise exception 'confidence total_weight mismatch';
    end if;
    if run_record.available_weight <> available_weight_expected then
        raise exception 'confidence available_weight mismatch';
    end if;
    if run_record.evidence_weight_coverage <> coverage_expected then
        raise exception 'confidence evidence coverage mismatch';
    end if;

    select count(*)
      into required_unavailable_count
      from zk.confidence_dimension_results r
      join zk.confidence_dimensions d
        on d.specification_id = run_record.specification_id
       and d.definition_version = run_record.definition_version
       and d.dimension_id = r.dimension_id
     where r.confidence_run_id = run_record.confidence_run_id
       and d.required
       and r.availability <> 'AVAILABLE';

    select count(*)
      into hard_floor_failure_count
      from zk.confidence_dimension_results
     where confidence_run_id = run_record.confidence_run_id
       and availability = 'AVAILABLE'
       and hard_floor_pass = false;

    if alpha_status <> 'SCORED' then
        decision_expected := 'NO_SIGNAL_ALPHA_UNAVAILABLE';
        score_expected := null;
    elsif required_unavailable_count > 0 then
        decision_expected := 'NO_SIGNAL_REQUIRED_EVIDENCE';
        score_expected := null;
    elsif coverage_expected < spec_record.minimum_weight_coverage then
        decision_expected := 'NO_SIGNAL_INSUFFICIENT_COVERAGE';
        score_expected := null;
    else
        select sum(weighted_contribution) / available_weight_expected
          into score_expected
          from zk.confidence_dimension_results
         where confidence_run_id = run_record.confidence_run_id
           and availability = 'AVAILABLE';

        if hard_floor_failure_count > 0 then
            decision_expected := 'NO_SIGNAL_HARD_FLOOR';
        elsif score_expected < spec_record.signal_eligibility_threshold then
            decision_expected := 'NO_SIGNAL_LOW_CONFIDENCE';
        else
            decision_expected := 'SIGNAL_ELIGIBLE';
        end if;
    end if;

    if run_record.decision <> decision_expected then
        raise exception 'confidence decision does not match evidence';
    end if;
    if run_record.confidence_score is distinct from score_expected then
        raise exception 'confidence score does not match evidence';
    end if;

    select count(*) into reason_count
      from zk.confidence_abstention_reasons
     where confidence_run_id = run_record.confidence_run_id;

    if decision_expected = 'SIGNAL_ELIGIBLE' then
        expected_reason_count := 0;
        if reason_count <> 0 then
            raise exception 'eligible confidence run cannot contain abstention reasons';
        end if;
    elsif decision_expected = 'NO_SIGNAL_ALPHA_UNAVAILABLE' then
        expected_reason_count := 1;
        if not exists (
            select 1 from zk.confidence_abstention_reasons
             where confidence_run_id = run_record.confidence_run_id
               and reason_code = 'ALPHA_UNAVAILABLE'
               and dimension_id is null
        ) then
            raise exception 'alpha-unavailable confidence run requires ALPHA_UNAVAILABLE reason';
        end if;
    elsif decision_expected = 'NO_SIGNAL_REQUIRED_EVIDENCE' then
        expected_reason_count := required_unavailable_count;
        if exists (
            select 1
              from zk.confidence_dimension_results r
              join zk.confidence_dimensions d
                on d.specification_id = run_record.specification_id
               and d.definition_version = run_record.definition_version
               and d.dimension_id = r.dimension_id
             where r.confidence_run_id = run_record.confidence_run_id
               and d.required
               and r.availability <> 'AVAILABLE'
               and not exists (
                   select 1
                     from zk.confidence_abstention_reasons ar
                    where ar.confidence_run_id = run_record.confidence_run_id
                      and ar.reason_code = 'REQUIRED_EVIDENCE'
                      and ar.dimension_id = r.dimension_id
               )
        ) then
            raise exception 'required-evidence confidence run is missing dimension reason';
        end if;
    elsif decision_expected = 'NO_SIGNAL_INSUFFICIENT_COVERAGE' then
        expected_reason_count := 1;
        if not exists (
            select 1 from zk.confidence_abstention_reasons
             where confidence_run_id = run_record.confidence_run_id
               and reason_code = 'INSUFFICIENT_CONFIDENCE_COVERAGE'
               and dimension_id is null
        ) then
            raise exception 'coverage-abstained confidence run requires coverage reason';
        end if;
    elsif decision_expected = 'NO_SIGNAL_HARD_FLOOR' then
        expected_reason_count := hard_floor_failure_count;
        if exists (
            select 1
              from zk.confidence_dimension_results r
             where r.confidence_run_id = run_record.confidence_run_id
               and r.availability = 'AVAILABLE'
               and r.hard_floor_pass = false
               and not exists (
                   select 1
                     from zk.confidence_abstention_reasons ar
                    where ar.confidence_run_id = run_record.confidence_run_id
                      and ar.reason_code = 'HARD_FLOOR'
                      and ar.dimension_id = r.dimension_id
               )
        ) then
            raise exception 'hard-floor confidence run is missing dimension reason';
        end if;
    else
        expected_reason_count := 1;
        if not exists (
            select 1 from zk.confidence_abstention_reasons
             where confidence_run_id = run_record.confidence_run_id
               and reason_code = 'LOW_CONFIDENCE_SCORE'
               and dimension_id is null
        ) then
            raise exception 'low-confidence run requires LOW_CONFIDENCE_SCORE reason';
        end if;
    end if;

    if reason_count <> expected_reason_count then
        raise exception 'confidence abstention reason count mismatch';
    end if;

    return new;
end;
$fn$;

create constraint trigger confidence_runs_complete_audit_trg
after insert on zk.confidence_runs
deferrable initially deferred
for each row execute function zk.audit_confidence_run_complete();

create index confidence_observations_security_dimension_idx
    on zk.confidence_observations(security_id, dimension_id, available_at desc);

create index confidence_runs_alpha_idx
    on zk.confidence_runs(alpha_run_id, prediction_timestamp desc);
