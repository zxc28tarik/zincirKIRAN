-- Zincir Kıran — Walk-Forward Tournament schema v0.1
-- OOS evidence only. No automatic challenger promotion path.

create table zk.tournament_specs (
    tournament_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    universe_rule_version text not null,
    evaluation_target text not null,
    hypothesis text not null,
    success_criteria text not null,
    preregistered_at timestamptz not null,
    purge_days integer not null,
    embargo_days integer not null,
    multiple_testing_method text not null,
    primary_metric_id text not null,
    stage text not null default 'CANDIDATE',
    created_at timestamptz not null default now(),
    primary key (tournament_id, definition_version),
    constraint tournament_specs_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint tournament_specs_purge_embargo_chk
        check (purge_days >= 0 and embargo_days >= 0),
    constraint tournament_specs_multiple_testing_chk
        check (multiple_testing_method = 'BENJAMINI_HOCHBERG'),
    constraint tournament_specs_candidate_only_chk
        check (stage = 'CANDIDATE'),
    constraint tournament_specs_text_chk
        check (
            length(trim(tournament_id)) > 0
            and length(trim(definition_version)) > 0
            and length(trim(universe_rule_version)) > 0
            and length(trim(evaluation_target)) > 0
            and length(trim(hypothesis)) > 0
            and length(trim(success_criteria)) > 0
            and length(trim(primary_metric_id)) > 0
        )
);

create function zk.reject_tournament_mutation()
returns trigger
language plpgsql
as $fn$
begin
    raise exception 'tournament records are append-only';
end;
$fn$;

create trigger tournament_specs_immutable_trg
before update or delete on zk.tournament_specs
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_contenders (
    tournament_id text not null,
    definition_version text not null,
    contender_id text not null,
    role text not null,
    artifact_kind text not null,
    artifact_specification_id text not null,
    artifact_definition_version text not null,
    rationale text not null,
    created_at timestamptz not null default now(),
    primary key (tournament_id, definition_version, contender_id),
    constraint tournament_contenders_spec_fk
        foreign key (tournament_id, definition_version)
        references zk.tournament_specs(tournament_id, definition_version),
    constraint tournament_contenders_role_chk
        check (role in ('CHAMPION', 'CHALLENGER')),
    constraint tournament_contenders_text_chk
        check (
            length(trim(contender_id)) > 0
            and length(trim(artifact_kind)) > 0
            and length(trim(artifact_specification_id)) > 0
            and length(trim(artifact_definition_version)) > 0
            and length(trim(rationale)) > 0
        )
);

create trigger tournament_contenders_immutable_trg
before update or delete on zk.tournament_contenders
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_folds (
    tournament_id text not null,
    definition_version text not null,
    fold_id text not null,
    train_start date not null,
    train_end date not null,
    validation_start date not null,
    validation_end date not null,
    created_at timestamptz not null default now(),
    primary key (tournament_id, definition_version, fold_id),
    constraint tournament_folds_spec_fk
        foreign key (tournament_id, definition_version)
        references zk.tournament_specs(tournament_id, definition_version),
    constraint tournament_folds_chronology_chk
        check (
            train_start <= train_end
            and train_end < validation_start
            and validation_start <= validation_end
        )
);

create function zk.validate_tournament_fold()
returns trigger
language plpgsql
as $fn$
declare
    purge_count integer;
    embargo_count integer;
begin
    select purge_days, embargo_days
      into purge_count, embargo_count
      from zk.tournament_specs
     where tournament_id = new.tournament_id
       and definition_version = new.definition_version;

    if (new.validation_start - new.train_end - 1) < purge_count then
        raise exception 'walk-forward fold violates purge_days';
    end if;

    if exists (
        select 1
          from zk.tournament_folds f
         where f.tournament_id = new.tournament_id
           and f.definition_version = new.definition_version
           and (
               (
                   f.validation_start < new.validation_start
                   and f.train_end >= new.train_end
               )
               or (
                   f.validation_start > new.validation_start
                   and f.train_end <= new.train_end
               )
           )
    ) then
        raise exception 'walk-forward train_end must advance across folds';
    end if;

    if exists (
        select 1
          from zk.tournament_folds f
         where f.tournament_id = new.tournament_id
           and f.definition_version = new.definition_version
           and daterange(
               f.validation_start,
               f.validation_end + 1,
               '[)'
           ) && daterange(
               new.validation_start,
               new.validation_end + 1,
               '[)'
           )
    ) then
        raise exception 'validation folds cannot overlap';
    end if;

    if exists (
        select 1
          from zk.tournament_folds f
         where f.tournament_id = new.tournament_id
           and f.definition_version = new.definition_version
           and (
               (
                   new.validation_start > f.validation_end
                   and (new.validation_start - f.validation_end - 1) < embargo_count
               )
               or (
                   f.validation_start > new.validation_end
                   and (f.validation_start - new.validation_end - 1) < embargo_count
               )
           )
    ) then
        raise exception 'walk-forward folds violate embargo_days';
    end if;

    return new;
end;
$fn$;

create trigger tournament_folds_validate_trg
before insert on zk.tournament_folds
for each row execute function zk.validate_tournament_fold();

create trigger tournament_folds_immutable_trg
before update or delete on zk.tournament_folds
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_metric_specs (
    tournament_id text not null,
    definition_version text not null,
    metric_id text not null,
    direction text not null,
    required boolean not null,
    requires_cost_model boolean not null default false,
    created_at timestamptz not null default now(),
    primary key (tournament_id, definition_version, metric_id),
    constraint tournament_metric_specs_spec_fk
        foreign key (tournament_id, definition_version)
        references zk.tournament_specs(tournament_id, definition_version),
    constraint tournament_metric_specs_direction_chk
        check (direction in ('HIGHER_IS_BETTER', 'LOWER_IS_BETTER')),
    constraint tournament_metric_specs_text_chk
        check (length(trim(metric_id)) > 0)
);

create trigger tournament_metric_specs_immutable_trg
before update or delete on zk.tournament_metric_specs
for each row execute function zk.reject_tournament_mutation();


create function zk.reject_tournament_structure_after_run()
returns trigger
language plpgsql
as $fn$
begin
    if exists (
        select 1
          from zk.tournament_runs r
         where r.tournament_id = new.tournament_id
           and r.definition_version = new.definition_version
    ) then
        raise exception 'tournament protocol structure is locked after first run';
    end if;
    return new;
end;
$fn$;

create table zk.tournament_runs (
    tournament_run_id text primary key,
    tournament_id text not null,
    definition_version text not null,
    data_snapshot_id text not null,
    executed_at timestamptz not null,
    created_at timestamptz not null default now(),
    constraint tournament_runs_spec_fk
        foreign key (tournament_id, definition_version)
        references zk.tournament_specs(tournament_id, definition_version),
    constraint tournament_runs_text_chk
        check (
            length(trim(tournament_run_id)) > 0
            and length(trim(data_snapshot_id)) > 0
        )
);


create trigger tournament_contenders_structure_lock_trg
before insert on zk.tournament_contenders
for each row execute function zk.reject_tournament_structure_after_run();

create trigger tournament_folds_structure_lock_trg
before insert on zk.tournament_folds
for each row execute function zk.reject_tournament_structure_after_run();

create trigger tournament_metric_specs_structure_lock_trg
before insert on zk.tournament_metric_specs
for each row execute function zk.reject_tournament_structure_after_run();

create function zk.validate_tournament_run()
returns trigger
language plpgsql
as $fn$
declare
    preregistered_time timestamptz;
begin
    select preregistered_at into preregistered_time
      from zk.tournament_specs
     where tournament_id = new.tournament_id
       and definition_version = new.definition_version;

    if preregistered_time > new.executed_at then
        raise exception 'tournament protocol was not preregistered before execution';
    end if;
    return new;
end;
$fn$;

create trigger tournament_runs_validate_trg
before insert on zk.tournament_runs
for each row execute function zk.validate_tournament_run();

create trigger tournament_runs_immutable_trg
before update or delete on zk.tournament_runs
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_fold_metrics (
    tournament_run_id text not null references zk.tournament_runs(tournament_run_id),
    contender_id text not null,
    fold_id text not null,
    metric_id text not null,
    metric_value numeric,
    sample_size integer not null,
    cost_model_id text,
    created_at timestamptz not null default now(),
    primary key (tournament_run_id, contender_id, fold_id, metric_id),
    constraint tournament_fold_metrics_sample_chk
        check (sample_size >= 0),
    constraint tournament_fold_metrics_value_chk
        check (
            metric_value is null
            or metric_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        )
);

create function zk.validate_tournament_fold_metric()
returns trigger
language plpgsql
as $fn$
declare
    spec_id text;
    spec_version text;
    requires_cost boolean;
begin
    select tournament_id, definition_version
      into spec_id, spec_version
      from zk.tournament_runs
     where tournament_run_id = new.tournament_run_id;

    if not exists (
        select 1
          from zk.tournament_contenders
         where tournament_id = spec_id
           and definition_version = spec_version
           and contender_id = new.contender_id
    ) then
        raise exception 'fold metric contender is not preregistered';
    end if;

    if not exists (
        select 1
          from zk.tournament_folds
         where tournament_id = spec_id
           and definition_version = spec_version
           and fold_id = new.fold_id
    ) then
        raise exception 'fold metric fold is not preregistered';
    end if;

    select requires_cost_model into requires_cost
      from zk.tournament_metric_specs
     where tournament_id = spec_id
       and definition_version = spec_version
       and metric_id = new.metric_id;

    if not found then
        raise exception 'fold metric is not preregistered';
    end if;

    if requires_cost and new.metric_value is not null then
        if new.cost_model_id is null or length(trim(new.cost_model_id)) = 0 then
            raise exception 'cost-aware fold metric requires cost_model_id';
        end if;
    end if;

    return new;
end;
$fn$;

create trigger tournament_fold_metrics_validate_trg
before insert on zk.tournament_fold_metrics
for each row execute function zk.validate_tournament_fold_metric();

create trigger tournament_fold_metrics_immutable_trg
before update or delete on zk.tournament_fold_metrics
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_aggregate_metrics (
    tournament_run_id text not null references zk.tournament_runs(tournament_run_id),
    contender_id text not null,
    metric_id text not null,
    valid_folds integer not null,
    total_folds integer not null,
    mean_value numeric,
    dispersion numeric,
    created_at timestamptz not null default now(),
    primary key (tournament_run_id, contender_id, metric_id),
    constraint tournament_aggregate_counts_chk
        check (
            valid_folds >= 0
            and total_folds >= 1
            and valid_folds <= total_folds
        ),
    constraint tournament_aggregate_value_chk
        check (
            (mean_value is null or mean_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric))
            and (dispersion is null or dispersion not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric))
        )
);

create trigger tournament_aggregate_metrics_immutable_trg
before update or delete on zk.tournament_aggregate_metrics
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_paired_differences (
    tournament_run_id text not null references zk.tournament_runs(tournament_run_id),
    challenger_id text not null,
    metric_id text not null,
    paired_folds integer not null,
    mean_difference_vs_champion numeric,
    created_at timestamptz not null default now(),
    primary key (tournament_run_id, challenger_id, metric_id),
    constraint tournament_paired_folds_chk check (paired_folds >= 0),
    constraint tournament_paired_value_chk
        check (
            mean_difference_vs_champion is null
            or mean_difference_vs_champion not in (
                'NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric
            )
        )
);

create trigger tournament_paired_differences_immutable_trg
before update or delete on zk.tournament_paired_differences
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_multiple_testing (
    tournament_run_id text not null references zk.tournament_runs(tournament_run_id),
    contender_id text not null,
    metric_id text not null,
    pvalue numeric not null,
    qvalue numeric not null,
    created_at timestamptz not null default now(),
    primary key (tournament_run_id, contender_id, metric_id),
    constraint tournament_multiple_testing_range_chk
        check (
            pvalue >= 0 and pvalue <= 1
            and qvalue >= 0 and qvalue <= 1
        )
);

create function zk.validate_tournament_multiple_testing_row()
returns trigger
language plpgsql
as $fn$
declare
    spec_id text;
    spec_version text;
begin
    select tournament_id, definition_version
      into spec_id, spec_version
      from zk.tournament_runs
     where tournament_run_id = new.tournament_run_id;

    if not exists (
        select 1
          from zk.tournament_contenders
         where tournament_id = spec_id
           and definition_version = spec_version
           and contender_id = new.contender_id
           and role = 'CHALLENGER'
    ) then
        raise exception 'multiple-testing evidence requires preregistered CHALLENGER';
    end if;

    if not exists (
        select 1
          from zk.tournament_metric_specs
         where tournament_id = spec_id
           and definition_version = spec_version
           and metric_id = new.metric_id
    ) then
        raise exception 'multiple-testing metric is not preregistered';
    end if;

    return new;
end;
$fn$;

create trigger tournament_multiple_testing_validate_trg
before insert on zk.tournament_multiple_testing
for each row execute function zk.validate_tournament_multiple_testing_row();

create trigger tournament_multiple_testing_immutable_trg
before update or delete on zk.tournament_multiple_testing
for each row execute function zk.reject_tournament_mutation();

create table zk.tournament_outcomes (
    tournament_run_id text primary key references zk.tournament_runs(tournament_run_id),
    champion_id text not null,
    decision text not null,
    automatic_promotion boolean not null,
    review_required boolean not null,
    primary_metric_id text not null,
    created_at timestamptz not null default now(),
    constraint tournament_outcome_decision_chk
        check (decision = 'RETAIN_CHAMPION_REVIEW_REQUIRED'),
    constraint tournament_outcome_no_auto_promotion_chk
        check (automatic_promotion = false and review_required = true)
);

create trigger tournament_outcomes_immutable_trg
before update or delete on zk.tournament_outcomes
for each row execute function zk.reject_tournament_mutation();

create function zk.audit_tournament_run_complete()
returns trigger
language plpgsql
as $fn$
declare
    run_record zk.tournament_runs%rowtype;
    spec_record zk.tournament_specs%rowtype;
    contender_count integer;
    champion_count integer;
    champion_id_value text;
    fold_count integer;
    metric_count integer;
    required_metric_count integer;
    expected_aggregate_count integer;
    actual_aggregate_count integer;
    expected_paired_count integer;
    actual_paired_count integer;
    outcome_count integer;
    primary_metric_exists boolean;
begin
    select * into run_record
      from zk.tournament_runs
     where tournament_run_id = new.tournament_run_id;

    select * into spec_record
      from zk.tournament_specs
     where tournament_id = run_record.tournament_id
       and definition_version = run_record.definition_version;

    select count(*),
           count(*) filter (where role = 'CHAMPION'),
           max(contender_id) filter (where role = 'CHAMPION')
      into contender_count, champion_count, champion_id_value
      from zk.tournament_contenders
     where tournament_id = run_record.tournament_id
       and definition_version = run_record.definition_version;

    if contender_count < 2 or champion_count <> 1 then
        raise exception 'tournament requires at least two contenders and exactly one champion';
    end if;

    select count(*) into fold_count
      from zk.tournament_folds
     where tournament_id = run_record.tournament_id
       and definition_version = run_record.definition_version;
    if fold_count < 2 then
        raise exception 'tournament requires at least two folds';
    end if;

    select count(*),
           count(*) filter (where required)
      into metric_count, required_metric_count
      from zk.tournament_metric_specs
     where tournament_id = run_record.tournament_id
       and definition_version = run_record.definition_version;
    if metric_count = 0 then
        raise exception 'tournament requires metric specifications';
    end if;

    select exists (
        select 1
          from zk.tournament_metric_specs
         where tournament_id = run_record.tournament_id
           and definition_version = run_record.definition_version
           and metric_id = spec_record.primary_metric_id
    ) into primary_metric_exists;
    if not primary_metric_exists then
        raise exception 'primary metric is not declared';
    end if;

    if exists (
        select 1
          from zk.tournament_metric_specs m
          cross join zk.tournament_contenders c
         where m.tournament_id = run_record.tournament_id
           and m.definition_version = run_record.definition_version
           and c.tournament_id = run_record.tournament_id
           and c.definition_version = run_record.definition_version
           and m.required
           and not exists (
               select 1
                 from zk.tournament_fold_metrics f
                where f.tournament_run_id = run_record.tournament_run_id
                  and f.contender_id = c.contender_id
                  and f.metric_id = m.metric_id
           )
    ) then
        raise exception 'required tournament metric has no OOS fold evidence';
    end if;

    expected_aggregate_count := contender_count * metric_count;
    select count(*) into actual_aggregate_count
      from zk.tournament_aggregate_metrics
     where tournament_run_id = run_record.tournament_run_id;
    if actual_aggregate_count <> expected_aggregate_count then
        raise exception 'tournament aggregate metric coverage mismatch';
    end if;

    if exists (
        with expected as (
            select c.contender_id,
                   m.metric_id,
                   count(f.metric_value) as valid_folds,
                   fold_count as total_folds,
                   avg(f.metric_value) as mean_value,
                   stddev_samp(f.metric_value) as dispersion
              from zk.tournament_contenders c
              cross join zk.tournament_metric_specs m
              left join zk.tournament_fold_metrics f
                on f.tournament_run_id = run_record.tournament_run_id
               and f.contender_id = c.contender_id
               and f.metric_id = m.metric_id
             where c.tournament_id = run_record.tournament_id
               and c.definition_version = run_record.definition_version
               and m.tournament_id = run_record.tournament_id
               and m.definition_version = run_record.definition_version
             group by c.contender_id, m.metric_id
        )
        select 1
          from expected e
          full join (
              select *
                from zk.tournament_aggregate_metrics
               where tournament_run_id = run_record.tournament_run_id
          ) a
            on a.contender_id = e.contender_id
           and a.metric_id = e.metric_id
         where e.contender_id is null
            or a.contender_id is null
            or a.valid_folds <> e.valid_folds
            or a.total_folds <> e.total_folds
            or a.mean_value is distinct from e.mean_value
            or a.dispersion is distinct from e.dispersion
    ) then
        raise exception 'tournament aggregate arithmetic mismatch';
    end if;

    expected_paired_count := (contender_count - 1) * metric_count;
    select count(*) into actual_paired_count
      from zk.tournament_paired_differences
     where tournament_run_id = run_record.tournament_run_id;
    if actual_paired_count <> expected_paired_count then
        raise exception 'tournament paired-difference coverage mismatch';
    end if;

    if exists (
        with challenger as (
            select contender_id
              from zk.tournament_contenders
             where tournament_id = run_record.tournament_id
               and definition_version = run_record.definition_version
               and role = 'CHALLENGER'
        ),
        expected as (
            select ch.contender_id as challenger_id,
                   m.metric_id,
                   count(*) filter (
                       where cf.metric_value is not null
                         and hf.metric_value is not null
                   ) as paired_folds,
                   avg(
                       case
                           when cf.metric_value is null or hf.metric_value is null
                               then null
                           when m.direction = 'LOWER_IS_BETTER'
                               then -(cf.metric_value - hf.metric_value)
                           else cf.metric_value - hf.metric_value
                       end
                   ) as mean_difference
              from challenger ch
              cross join zk.tournament_metric_specs m
              cross join zk.tournament_folds wf
              left join zk.tournament_fold_metrics cf
                on cf.tournament_run_id = run_record.tournament_run_id
               and cf.contender_id = ch.contender_id
               and cf.fold_id = wf.fold_id
               and cf.metric_id = m.metric_id
              left join zk.tournament_fold_metrics hf
                on hf.tournament_run_id = run_record.tournament_run_id
               and hf.contender_id = champion_id_value
               and hf.fold_id = wf.fold_id
               and hf.metric_id = m.metric_id
             where m.tournament_id = run_record.tournament_id
               and m.definition_version = run_record.definition_version
               and wf.tournament_id = run_record.tournament_id
               and wf.definition_version = run_record.definition_version
             group by ch.contender_id, m.metric_id
        )
        select 1
          from expected e
          full join (
              select *
                from zk.tournament_paired_differences
               where tournament_run_id = run_record.tournament_run_id
          ) p
            on p.challenger_id = e.challenger_id
           and p.metric_id = e.metric_id
         where e.challenger_id is null
            or p.challenger_id is null
            or p.paired_folds <> e.paired_folds
            or p.mean_difference_vs_champion is distinct from e.mean_difference
    ) then
        raise exception 'tournament paired-difference arithmetic mismatch';
    end if;

    if exists (
        with ranked as (
            select contender_id,
                   metric_id,
                   pvalue,
                   qvalue,
                   row_number() over (order by pvalue, contender_id, metric_id) as rank_no,
                   count(*) over () as test_count
              from zk.tournament_multiple_testing
             where tournament_run_id = run_record.tournament_run_id
        ),
        raw as (
            select *,
                   least(1::numeric, pvalue * test_count / rank_no) as raw_q
              from ranked
        ),
        expected as (
            select *,
                   min(raw_q) over (
                       order by rank_no desc
                       rows between unbounded preceding and current row
                   ) as expected_q
              from raw
        )
        select 1
          from expected
         where qvalue <> expected_q
    ) then
        raise exception 'tournament Benjamini-Hochberg qvalue mismatch';
    end if;

    select count(*) into outcome_count
      from zk.tournament_outcomes
     where tournament_run_id = run_record.tournament_run_id;
    if outcome_count <> 1 then
        raise exception 'tournament requires exactly one outcome';
    end if;

    if exists (
        select 1
          from zk.tournament_outcomes o
         where o.tournament_run_id = run_record.tournament_run_id
           and (
               o.champion_id <> champion_id_value
               or o.primary_metric_id <> spec_record.primary_metric_id
               or o.decision <> 'RETAIN_CHAMPION_REVIEW_REQUIRED'
               or o.automatic_promotion
               or not o.review_required
           )
    ) then
        raise exception 'tournament outcome attempted automatic promotion or mismatched champion';
    end if;

    return new;
end;
$fn$;

create constraint trigger tournament_runs_complete_audit_trg
after insert on zk.tournament_runs
deferrable initially deferred
for each row execute function zk.audit_tournament_run_complete();

create constraint trigger tournament_fold_metrics_complete_audit_trg
after insert on zk.tournament_fold_metrics
deferrable initially deferred
for each row execute function zk.audit_tournament_run_complete();

create constraint trigger tournament_aggregate_metrics_complete_audit_trg
after insert on zk.tournament_aggregate_metrics
deferrable initially deferred
for each row execute function zk.audit_tournament_run_complete();

create constraint trigger tournament_paired_differences_complete_audit_trg
after insert on zk.tournament_paired_differences
deferrable initially deferred
for each row execute function zk.audit_tournament_run_complete();

create constraint trigger tournament_multiple_testing_complete_audit_trg
after insert on zk.tournament_multiple_testing
deferrable initially deferred
for each row execute function zk.audit_tournament_run_complete();

create constraint trigger tournament_outcomes_complete_audit_trg
after insert on zk.tournament_outcomes
deferrable initially deferred
for each row execute function zk.audit_tournament_run_complete();

create index tournament_fold_metrics_lookup_idx
    on zk.tournament_fold_metrics(tournament_run_id, contender_id, metric_id, fold_id);
