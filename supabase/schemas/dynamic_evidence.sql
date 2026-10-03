-- Zincir Kıran — Dynamic Evidence Weighting schema v0.1
-- Research-candidate only. No production promotion path is defined here.

create table zk.dynamic_weighting_specs (
    specification_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    base_alpha_specification_id text not null,
    base_alpha_definition_version text not null,
    minimum_metric_coverage numeric not null,
    max_evidence_age_days integer not null,
    multiplier_floor numeric not null,
    multiplier_ceiling numeric not null,
    gross_exposure_policy text not null,
    stage text not null default 'CANDIDATE',
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint dynamic_weighting_base_alpha_fk
        foreign key (base_alpha_specification_id, base_alpha_definition_version)
        references zk.alpha_aggregation_specs(specification_id, definition_version),
    constraint dynamic_weighting_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint dynamic_weighting_coverage_chk
        check (minimum_metric_coverage >= 0 and minimum_metric_coverage <= 1),
    constraint dynamic_weighting_age_chk
        check (max_evidence_age_days >= 0),
    constraint dynamic_weighting_multiplier_chk
        check (
            multiplier_floor > 0
            and multiplier_ceiling >= multiplier_floor
            and multiplier_floor not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and multiplier_ceiling not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint dynamic_weighting_gross_policy_chk
        check (gross_exposure_policy in ('NONE', 'PRESERVE_BASE_ABS_SUM')),
    constraint dynamic_weighting_candidate_only_chk
        check (stage = 'CANDIDATE'),
    constraint dynamic_weighting_text_chk
        check (
            length(trim(specification_id)) > 0
            and length(trim(definition_version)) > 0
        )
);

create function zk.reject_dynamic_weighting_mutation()
returns trigger
language plpgsql
as $fn$
begin
    raise exception 'dynamic evidence weighting records are append-only';
end;
$fn$;

create function zk.validate_dynamic_weighting_spec()
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
        raise exception 'dynamic weighting horizon does not match base alpha specification';
    end if;
    return new;
end;
$fn$;

create trigger dynamic_weighting_specs_validate_trg
before insert on zk.dynamic_weighting_specs
for each row execute function zk.validate_dynamic_weighting_spec();

create trigger dynamic_weighting_specs_immutable_trg
before update or delete on zk.dynamic_weighting_specs
for each row execute function zk.reject_dynamic_weighting_mutation();

create table zk.dynamic_evidence_terms (
    specification_id text not null,
    definition_version text not null,
    metric_id text not null,
    normalization_rule_id text not null,
    bad_reference numeric not null,
    good_reference numeric not null,
    coefficient numeric not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, metric_id),
    constraint dynamic_evidence_terms_spec_fk
        foreign key (specification_id, definition_version)
        references zk.dynamic_weighting_specs(specification_id, definition_version),
    constraint dynamic_evidence_terms_reference_chk
        check (
            bad_reference <> good_reference
            and bad_reference not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and good_reference not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint dynamic_evidence_terms_coefficient_chk
        check (
            coefficient > 0
            and coefficient not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint dynamic_evidence_terms_text_chk
        check (
            length(trim(metric_id)) > 0
            and length(trim(normalization_rule_id)) > 0
        )
);

create trigger dynamic_evidence_terms_immutable_trg
before update or delete on zk.dynamic_evidence_terms
for each row execute function zk.reject_dynamic_weighting_mutation();

create table zk.dynamic_evidence_snapshots (
    snapshot_id text primary key,
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    evidence_protocol_id text not null,
    window_start timestamptz not null,
    window_end timestamptz not null,
    available_at timestamptz not null,
    created_at timestamptz not null default now(),
    constraint dynamic_evidence_snapshot_time_chk
        check (window_start <= window_end and window_end <= available_at),
    constraint dynamic_evidence_snapshot_text_chk
        check (
            length(trim(snapshot_id)) > 0
            and length(trim(evidence_protocol_id)) > 0
        )
);

create trigger dynamic_evidence_snapshots_immutable_trg
before update or delete on zk.dynamic_evidence_snapshots
for each row execute function zk.reject_dynamic_weighting_mutation();

create table zk.dynamic_evidence_metric_values (
    snapshot_id text not null references zk.dynamic_evidence_snapshots(snapshot_id),
    metric_id text not null,
    raw_value numeric not null,
    created_at timestamptz not null default now(),
    primary key (snapshot_id, metric_id),
    constraint dynamic_evidence_metric_value_chk
        check (
            raw_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint dynamic_evidence_metric_text_chk
        check (length(trim(metric_id)) > 0)
);

create trigger dynamic_evidence_metric_values_immutable_trg
before update or delete on zk.dynamic_evidence_metric_values
for each row execute function zk.reject_dynamic_weighting_mutation();

create table zk.dynamic_weight_runs (
    dynamic_run_id text primary key,
    specification_id text not null,
    definition_version text not null,
    prediction_timestamp timestamptz not null,
    status text not null,
    base_gross_exposure numeric not null,
    preliminary_gross_exposure numeric,
    resolved_gross_exposure numeric,
    gross_rescale_factor numeric,
    created_at timestamptz not null default now(),
    constraint dynamic_weight_runs_spec_fk
        foreign key (specification_id, definition_version)
        references zk.dynamic_weighting_specs(specification_id, definition_version),
    constraint dynamic_weight_runs_status_chk
        check (status in ('RESOLVED', 'ABSTAIN_INSUFFICIENT_EVIDENCE')),
    constraint dynamic_weight_runs_base_gross_chk
        check (
            base_gross_exposure > 0
            and base_gross_exposure not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint dynamic_weight_runs_resolution_chk
        check (
            (
                status = 'RESOLVED'
                and preliminary_gross_exposure is not null
                and resolved_gross_exposure is not null
                and gross_rescale_factor is not null
            )
            or (
                status = 'ABSTAIN_INSUFFICIENT_EVIDENCE'
                and preliminary_gross_exposure is null
                and resolved_gross_exposure is null
                and gross_rescale_factor is null
            )
        )
);

create trigger dynamic_weight_runs_immutable_trg
before update or delete on zk.dynamic_weight_runs
for each row execute function zk.reject_dynamic_weighting_mutation();

create table zk.dynamic_weight_factor_results (
    dynamic_run_id text not null references zk.dynamic_weight_runs(dynamic_run_id),
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    snapshot_id text not null references zk.dynamic_evidence_snapshots(snapshot_id),
    base_weight numeric not null,
    evidence_coverage numeric not null,
    evidence_score numeric not null,
    multiplier numeric not null,
    preliminary_weight numeric not null,
    final_weight numeric,
    created_at timestamptz not null default now(),
    primary key (dynamic_run_id, admission_id),
    constraint dynamic_factor_coverage_chk
        check (evidence_coverage >= 0 and evidence_coverage <= 1),
    constraint dynamic_factor_score_chk
        check (evidence_score >= 0 and evidence_score <= 1),
    constraint dynamic_factor_numeric_chk
        check (
            base_weight <> 0
            and multiplier > 0
            and preliminary_weight <> 0
            and base_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and evidence_score not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and multiplier not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and preliminary_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and (
                final_weight is null
                or final_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            )
        )
);

create function zk.validate_dynamic_factor_result()
returns trigger
language plpgsql
as $fn$
declare
    run_status text;
    prediction_time timestamptz;
    spec_base_id text;
    spec_base_version text;
    max_age integer;
    expected_base_weight numeric;
    snapshot_admission text;
    snapshot_window_end timestamptz;
    snapshot_available_at timestamptz;
begin
    select r.status, r.prediction_timestamp,
           s.base_alpha_specification_id, s.base_alpha_definition_version,
           s.max_evidence_age_days
      into run_status, prediction_time, spec_base_id, spec_base_version, max_age
      from zk.dynamic_weight_runs r
      join zk.dynamic_weighting_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where r.dynamic_run_id = new.dynamic_run_id;

    select weight into expected_base_weight
      from zk.alpha_factor_weights
     where specification_id = spec_base_id
       and definition_version = spec_base_version
       and admission_id = new.admission_id;

    if expected_base_weight is null or expected_base_weight <> new.base_weight then
        raise exception 'dynamic factor result base_weight does not match base alpha plan';
    end if;

    select admission_id, window_end, available_at
      into snapshot_admission, snapshot_window_end, snapshot_available_at
      from zk.dynamic_evidence_snapshots
     where snapshot_id = new.snapshot_id;

    if snapshot_admission <> new.admission_id then
        raise exception 'dynamic evidence snapshot admission mismatch';
    end if;
    if snapshot_window_end > prediction_time or snapshot_available_at > prediction_time then
        raise exception 'future evidence cannot enter dynamic weighting';
    end if;
    if extract(epoch from (prediction_time - snapshot_window_end)) / 86400 > max_age then
        raise exception 'stale evidence cannot produce a resolved factor result';
    end if;

    if sign(new.preliminary_weight) <> sign(new.base_weight) then
        raise exception 'dynamic multiplier cannot flip base-weight sign';
    end if;
    if new.final_weight is not null and sign(new.final_weight) <> sign(new.base_weight) then
        raise exception 'dynamic final weight cannot flip base-weight sign';
    end if;
    if run_status = 'RESOLVED' and new.final_weight is null then
        raise exception 'resolved dynamic run requires final_weight';
    end if;
    if run_status = 'ABSTAIN_INSUFFICIENT_EVIDENCE' and new.final_weight is not null then
        raise exception 'abstained dynamic run cannot emit final weights';
    end if;
    return new;
end;
$fn$;

create trigger dynamic_weight_factor_results_validate_trg
before insert on zk.dynamic_weight_factor_results
for each row execute function zk.validate_dynamic_factor_result();

create trigger dynamic_weight_factor_results_immutable_trg
before update or delete on zk.dynamic_weight_factor_results
for each row execute function zk.reject_dynamic_weighting_mutation();

create table zk.dynamic_weight_metric_contributions (
    dynamic_run_id text not null,
    admission_id text not null,
    metric_id text not null,
    normalization_rule_id text not null,
    raw_value numeric not null,
    normalized_quality numeric not null,
    coefficient numeric not null,
    weighted_quality_contribution numeric not null,
    created_at timestamptz not null default now(),
    primary key (dynamic_run_id, admission_id, metric_id),
    constraint dynamic_metric_factor_fk
        foreign key (dynamic_run_id, admission_id)
        references zk.dynamic_weight_factor_results(dynamic_run_id, admission_id),
    constraint dynamic_metric_quality_chk
        check (normalized_quality >= 0 and normalized_quality <= 1),
    constraint dynamic_metric_numeric_chk
        check (
            coefficient > 0
            and raw_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and normalized_quality not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and coefficient not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and weighted_quality_contribution not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        )
);

create function zk.validate_dynamic_metric_contribution()
returns trigger
language plpgsql
as $fn$
declare
    spec_id text;
    spec_version text;
    snapshot_key text;
    expected_normalization text;
    bad_ref numeric;
    good_ref numeric;
    expected_coefficient numeric;
    expected_raw numeric;
    expected_quality numeric;
begin
    select r.specification_id, r.definition_version, f.snapshot_id
      into spec_id, spec_version, snapshot_key
      from zk.dynamic_weight_factor_results f
      join zk.dynamic_weight_runs r on r.dynamic_run_id = f.dynamic_run_id
     where f.dynamic_run_id = new.dynamic_run_id
       and f.admission_id = new.admission_id;

    select normalization_rule_id, bad_reference, good_reference, coefficient
      into expected_normalization, bad_ref, good_ref, expected_coefficient
      from zk.dynamic_evidence_terms
     where specification_id = spec_id
       and definition_version = spec_version
       and metric_id = new.metric_id;

    if expected_normalization is null then
        raise exception 'metric contribution is not declared in dynamic weighting specification';
    end if;

    select raw_value into expected_raw
      from zk.dynamic_evidence_metric_values
     where snapshot_id = snapshot_key
       and metric_id = new.metric_id;

    if expected_raw is null then
        raise exception 'metric contribution is missing from evidence snapshot';
    end if;
    if new.normalization_rule_id <> expected_normalization then
        raise exception 'metric contribution normalization rule mismatch';
    end if;
    if new.coefficient <> expected_coefficient then
        raise exception 'metric contribution coefficient mismatch';
    end if;
    if new.raw_value <> expected_raw then
        raise exception 'metric contribution raw value mismatch';
    end if;

    expected_quality := least(
        1::numeric,
        greatest(0::numeric, (new.raw_value - bad_ref) / (good_ref - bad_ref))
    );
    if new.normalized_quality <> expected_quality then
        raise exception 'metric contribution normalized quality mismatch';
    end if;
    if new.weighted_quality_contribution <> new.normalized_quality * new.coefficient then
        raise exception 'metric weighted quality arithmetic mismatch';
    end if;
    return new;
end;
$fn$;

create trigger dynamic_weight_metric_contributions_validate_trg
before insert on zk.dynamic_weight_metric_contributions
for each row execute function zk.validate_dynamic_metric_contribution();

create trigger dynamic_weight_metric_contributions_immutable_trg
before update or delete on zk.dynamic_weight_metric_contributions
for each row execute function zk.reject_dynamic_weighting_mutation();

create table zk.dynamic_weight_insufficient_factors (
    dynamic_run_id text not null references zk.dynamic_weight_runs(dynamic_run_id),
    admission_id text not null references zk.alpha_factor_admissions(admission_id),
    reason text not null,
    snapshot_id text references zk.dynamic_evidence_snapshots(snapshot_id),
    created_at timestamptz not null default now(),
    primary key (dynamic_run_id, admission_id),
    constraint dynamic_insufficient_reason_chk
        check (reason in (
            'MISSING_SNAPSHOT', 'STALE_EVIDENCE', 'INSUFFICIENT_METRIC_COVERAGE'
        ))
);

create function zk.validate_dynamic_insufficient_factor()
returns trigger
language plpgsql
as $fn$
declare
    run_status text;
    prediction_time timestamptz;
    spec_id text;
    spec_version text;
    base_spec_id text;
    base_spec_version text;
    max_age integer;
    min_coverage numeric;
    snapshot_admission text;
    snapshot_window_end timestamptz;
    snapshot_available_at timestamptz;
    total_coefficient numeric;
    available_coefficient numeric;
    metric_coverage numeric;
begin
    select r.status, r.prediction_timestamp, r.specification_id, r.definition_version,
           s.base_alpha_specification_id, s.base_alpha_definition_version,
           s.max_evidence_age_days, s.minimum_metric_coverage
      into run_status, prediction_time, spec_id, spec_version,
           base_spec_id, base_spec_version, max_age, min_coverage
      from zk.dynamic_weight_runs r
      join zk.dynamic_weighting_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where r.dynamic_run_id = new.dynamic_run_id;

    if run_status <> 'ABSTAIN_INSUFFICIENT_EVIDENCE' then
        raise exception 'insufficient factor records require an abstained dynamic run';
    end if;

    if not exists (
        select 1 from zk.alpha_factor_weights
         where specification_id = base_spec_id
           and definition_version = base_spec_version
           and admission_id = new.admission_id
    ) then
        raise exception 'insufficient factor is not part of the base alpha plan';
    end if;

    if new.reason = 'MISSING_SNAPSHOT' then
        if new.snapshot_id is not null then
            raise exception 'MISSING_SNAPSHOT reason cannot carry snapshot_id';
        end if;
        return new;
    end if;

    if new.snapshot_id is null then
        raise exception 'stale/coverage insufficiency requires snapshot_id';
    end if;

    select admission_id, window_end, available_at
      into snapshot_admission, snapshot_window_end, snapshot_available_at
      from zk.dynamic_evidence_snapshots
     where snapshot_id = new.snapshot_id;

    if snapshot_admission <> new.admission_id then
        raise exception 'insufficient evidence snapshot admission mismatch';
    end if;
    if snapshot_window_end > prediction_time or snapshot_available_at > prediction_time then
        raise exception 'future evidence cannot be recorded as insufficient historical evidence';
    end if;

    if new.reason = 'STALE_EVIDENCE' then
        if extract(epoch from (prediction_time - snapshot_window_end)) / 86400 <= max_age then
            raise exception 'STALE_EVIDENCE reason requires evidence older than max age';
        end if;
        return new;
    end if;

    if extract(epoch from (prediction_time - snapshot_window_end)) / 86400 > max_age then
        raise exception 'stale evidence must use STALE_EVIDENCE reason';
    end if;

    select sum(coefficient) into total_coefficient
      from zk.dynamic_evidence_terms
     where specification_id = spec_id
       and definition_version = spec_version;

    select coalesce(sum(t.coefficient), 0)
      into available_coefficient
      from zk.dynamic_evidence_terms t
     where t.specification_id = spec_id
       and t.definition_version = spec_version
       and exists (
           select 1
             from zk.dynamic_evidence_metric_values m
            where m.snapshot_id = new.snapshot_id
              and m.metric_id = t.metric_id
       );

    metric_coverage := available_coefficient / total_coefficient;
    if metric_coverage >= min_coverage then
        raise exception 'INSUFFICIENT_METRIC_COVERAGE reason requires coverage below threshold';
    end if;
    return new;
end;
$fn$;

create trigger dynamic_weight_insufficient_factors_validate_trg
before insert on zk.dynamic_weight_insufficient_factors
for each row execute function zk.validate_dynamic_insufficient_factor();

create trigger dynamic_weight_insufficient_factors_immutable_trg
before update or delete on zk.dynamic_weight_insufficient_factors
for each row execute function zk.reject_dynamic_weighting_mutation();

create function zk.audit_dynamic_weight_run_complete()
returns trigger
language plpgsql
as $fn$
declare
    run_record zk.dynamic_weight_runs%rowtype;
    spec_record zk.dynamic_weighting_specs%rowtype;
    base_count integer;
    base_gross numeric;
    result_count integer;
    insufficient_count integer;
    prelim_gross numeric;
    final_gross numeric;
    expected_scale numeric;
    invalid_factor_count integer;
begin
    select * into run_record
      from zk.dynamic_weight_runs
     where dynamic_run_id = new.dynamic_run_id;

    select * into spec_record
      from zk.dynamic_weighting_specs
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    select count(*), coalesce(sum(abs(weight)), 0)
      into base_count, base_gross
      from zk.alpha_factor_weights
     where specification_id = spec_record.base_alpha_specification_id
       and definition_version = spec_record.base_alpha_definition_version;

    if base_count = 0 then
        raise exception 'dynamic weighting run requires a non-empty base alpha plan';
    end if;
    if run_record.base_gross_exposure <> base_gross then
        raise exception 'dynamic run base_gross_exposure does not match base alpha plan';
    end if;

    select count(*), coalesce(sum(abs(preliminary_weight)), 0),
           coalesce(sum(abs(final_weight)), 0)
      into result_count, prelim_gross, final_gross
      from zk.dynamic_weight_factor_results
     where dynamic_run_id = new.dynamic_run_id;

    select count(*) into insufficient_count
      from zk.dynamic_weight_insufficient_factors
     where dynamic_run_id = new.dynamic_run_id;

    if exists (
        select 1
          from zk.dynamic_weight_factor_results r
          join zk.dynamic_weight_insufficient_factors i
            on i.dynamic_run_id = r.dynamic_run_id
           and i.admission_id = r.admission_id
         where r.dynamic_run_id = new.dynamic_run_id
    ) then
        raise exception 'dynamic factor cannot be both resolved and insufficient';
    end if;

    if result_count + insufficient_count <> base_count then
        raise exception 'dynamic run does not account for every base alpha factor';
    end if;

    select count(*) into invalid_factor_count
      from zk.dynamic_weight_factor_results f
     where f.dynamic_run_id = new.dynamic_run_id
       and not exists (
           select 1
             from zk.alpha_factor_weights w
            where w.specification_id = spec_record.base_alpha_specification_id
              and w.definition_version = spec_record.base_alpha_definition_version
              and w.admission_id = f.admission_id
       );
    if invalid_factor_count > 0 then
        raise exception 'dynamic run contains factor outside base alpha plan';
    end if;

    if exists (
        select 1
          from zk.dynamic_weight_factor_results f
         where f.dynamic_run_id = new.dynamic_run_id
           and (
               select coalesce(sum(t.coefficient), 0)
                 from zk.dynamic_evidence_terms t
                where t.specification_id = run_record.specification_id
                  and t.definition_version = run_record.definition_version
           ) = 0
    ) then
        raise exception 'dynamic weighting specification requires evidence terms';
    end if;

    if exists (
        select 1
          from zk.dynamic_weight_factor_results f
         where f.dynamic_run_id = new.dynamic_run_id
           and (
               f.evidence_coverage <> (
                   select coalesce(sum(c.coefficient), 0) /
                          (select sum(t.coefficient)
                             from zk.dynamic_evidence_terms t
                            where t.specification_id = run_record.specification_id
                              and t.definition_version = run_record.definition_version)
                     from zk.dynamic_weight_metric_contributions c
                    where c.dynamic_run_id = f.dynamic_run_id
                      and c.admission_id = f.admission_id
               )
               or f.evidence_score <> (
                   select sum(c.weighted_quality_contribution) / sum(c.coefficient)
                     from zk.dynamic_weight_metric_contributions c
                    where c.dynamic_run_id = f.dynamic_run_id
                      and c.admission_id = f.admission_id
               )
               or f.multiplier <> (
                   spec_record.multiplier_floor
                   + f.evidence_score
                     * (spec_record.multiplier_ceiling - spec_record.multiplier_floor)
               )
               or f.preliminary_weight <> f.base_weight * f.multiplier
               or f.evidence_coverage < spec_record.minimum_metric_coverage
           )
    ) then
        raise exception 'dynamic factor evidence arithmetic is inconsistent';
    end if;

    if run_record.status = 'RESOLVED' then
        if insufficient_count <> 0 or result_count <> base_count then
            raise exception 'resolved dynamic run must resolve every base alpha factor';
        end if;
        if run_record.preliminary_gross_exposure <> prelim_gross then
            raise exception 'preliminary gross exposure mismatch';
        end if;

        if spec_record.gross_exposure_policy = 'PRESERVE_BASE_ABS_SUM' then
            expected_scale := base_gross / prelim_gross;
        else
            expected_scale := 1;
        end if;

        if run_record.gross_rescale_factor <> expected_scale then
            raise exception 'dynamic run gross rescale factor mismatch';
        end if;

        if exists (
            select 1 from zk.dynamic_weight_factor_results f
             where f.dynamic_run_id = new.dynamic_run_id
               and f.final_weight <> f.preliminary_weight * expected_scale
        ) then
            raise exception 'dynamic final weight rescaling is inconsistent';
        end if;

        if run_record.resolved_gross_exposure <> final_gross then
            raise exception 'resolved gross exposure mismatch';
        end if;
        if spec_record.gross_exposure_policy = 'PRESERVE_BASE_ABS_SUM'
           and final_gross <> base_gross then
            raise exception 'preserved gross exposure does not match base gross';
        end if;
    else
        if insufficient_count = 0 then
            raise exception 'abstained dynamic run requires at least one insufficient factor';
        end if;
    end if;

    return new;
end;
$fn$;

create constraint trigger dynamic_weight_runs_complete_audit_trg
after insert on zk.dynamic_weight_runs
deferrable initially deferred
for each row execute function zk.audit_dynamic_weight_run_complete();

create index dynamic_evidence_snapshot_admission_idx
    on zk.dynamic_evidence_snapshots(admission_id, available_at desc);

create index dynamic_weight_runs_prediction_idx
    on zk.dynamic_weight_runs(prediction_timestamp desc);
