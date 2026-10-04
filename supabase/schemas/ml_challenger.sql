-- Zincir Kıran — ML Challenger schema v0.1
-- Candidate-only ML evidence. No automatic production-promotion path.

create table zk.ml_challenger_specs (
    challenger_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    universe_rule_version text not null,
    evaluation_target text not null,
    ridge_penalty numeric not null,
    random_seed integer not null,
    preregistered_at timestamptz not null,
    stage text not null default 'CANDIDATE',
    created_at timestamptz not null default now(),
    primary key (challenger_id, definition_version),
    constraint ml_specs_horizon_chk check (horizon_days in (20, 60, 120, 252)),
    constraint ml_specs_penalty_chk check (ridge_penalty >= 0),
    constraint ml_specs_candidate_only_chk check (stage = 'CANDIDATE'),
    constraint ml_specs_text_chk check (
        length(trim(challenger_id)) > 0
        and length(trim(definition_version)) > 0
        and length(trim(universe_rule_version)) > 0
        and length(trim(evaluation_target)) > 0
    )
);

create function zk.reject_ml_challenger_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'ML challenger records are append-only';
end;
$fn$;

create trigger ml_challenger_specs_immutable_trg
before update or delete on zk.ml_challenger_specs
for each row execute function zk.reject_ml_challenger_mutation();

create table zk.ml_challenger_features (
    challenger_id text not null,
    definition_version text not null,
    feature_id text not null,
    ordinal integer not null,
    created_at timestamptz not null default now(),
    primary key (challenger_id, definition_version, feature_id),
    unique (challenger_id, definition_version, ordinal),
    foreign key (challenger_id, definition_version)
        references zk.ml_challenger_specs(challenger_id, definition_version),
    constraint ml_features_ordinal_chk check (ordinal >= 0),
    constraint ml_features_text_chk check (length(trim(feature_id)) > 0)
);

create trigger ml_challenger_features_immutable_trg
before update or delete on zk.ml_challenger_features
for each row execute function zk.reject_ml_challenger_mutation();

create table zk.ml_challenger_fits (
    fit_id text primary key,
    challenger_id text not null,
    definition_version text not null,
    data_snapshot_id text not null,
    fit_at timestamptz not null,
    training_cutoff timestamptz not null,
    training_observations integer not null,
    model_artifact_hash text not null,
    created_at timestamptz not null default now(),
    foreign key (challenger_id, definition_version)
        references zk.ml_challenger_specs(challenger_id, definition_version),
    constraint ml_fits_count_chk check (training_observations > 0),
    constraint ml_fits_text_chk check (
        length(trim(fit_id)) > 0
        and length(trim(data_snapshot_id)) > 0
        and length(trim(model_artifact_hash)) > 0
    ),
    constraint ml_fits_cutoff_chk check (training_cutoff < fit_at)
);

create function zk.validate_ml_challenger_fit()
returns trigger language plpgsql as $fn$
declare
    preregistered_time timestamptz;
begin
    select preregistered_at into preregistered_time
      from zk.ml_challenger_specs
     where challenger_id = new.challenger_id
       and definition_version = new.definition_version;

    if preregistered_time >= new.fit_at then
        raise exception 'ML challenger fit must follow preregistration';
    end if;

    if not exists (
        select 1 from zk.ml_challenger_features
         where challenger_id = new.challenger_id
           and definition_version = new.definition_version
    ) then
        raise exception 'ML challenger fit requires preregistered features';
    end if;

    return new;
end;
$fn$;

create trigger ml_challenger_fits_validate_trg
before insert on zk.ml_challenger_fits
for each row execute function zk.validate_ml_challenger_fit();

create trigger ml_challenger_fits_immutable_trg
before update or delete on zk.ml_challenger_fits
for each row execute function zk.reject_ml_challenger_mutation();

create table zk.ml_training_observations (
    fit_id text not null references zk.ml_challenger_fits(fit_id),
    security_id text not null,
    observation_at timestamptz not null,
    target_available_at timestamptz not null,
    target_value numeric not null,
    created_at timestamptz not null default now(),
    primary key (fit_id, security_id, observation_at),
    constraint ml_training_security_chk check (length(trim(security_id)) > 0),
    constraint ml_training_target_chk check (
        target_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    )
);

create function zk.validate_ml_training_observation()
returns trigger language plpgsql as $fn$
declare
    fit_time timestamptz;
    cutoff_time timestamptz;
begin
    select fit_at, training_cutoff into fit_time, cutoff_time
      from zk.ml_challenger_fits where fit_id = new.fit_id;

    if new.observation_at > cutoff_time then
        raise exception 'training observation exceeds preregistered cutoff';
    end if;
    if new.target_available_at > fit_time then
        raise exception 'future target evidence is forbidden';
    end if;
    return new;
end;
$fn$;

create trigger ml_training_observations_validate_trg
before insert on zk.ml_training_observations
for each row execute function zk.validate_ml_training_observation();

create trigger ml_training_observations_immutable_trg
before update or delete on zk.ml_training_observations
for each row execute function zk.reject_ml_challenger_mutation();

create table zk.ml_feature_observations (
    fit_id text not null references zk.ml_challenger_fits(fit_id),
    security_id text not null,
    observation_at timestamptz not null,
    feature_id text not null,
    feature_value numeric not null,
    available_at timestamptz not null,
    created_at timestamptz not null default now(),
    primary key (fit_id, security_id, observation_at, feature_id),
    constraint ml_feature_value_chk check (
        feature_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    )
);

create function zk.validate_ml_feature_observation()
returns trigger language plpgsql as $fn$
declare
    spec_id text;
    spec_version text;
begin
    select challenger_id, definition_version into spec_id, spec_version
      from zk.ml_challenger_fits where fit_id = new.fit_id;

    if new.available_at > new.observation_at then
        raise exception 'future feature evidence is forbidden';
    end if;

    if not exists (
        select 1 from zk.ml_challenger_features
         where challenger_id = spec_id
           and definition_version = spec_version
           and feature_id = new.feature_id
    ) then
        raise exception 'feature is not preregistered for ML challenger';
    end if;
    return new;
end;
$fn$;

create trigger ml_feature_observations_validate_trg
before insert on zk.ml_feature_observations
for each row execute function zk.validate_ml_feature_observation();

create trigger ml_feature_observations_immutable_trg
before update or delete on zk.ml_feature_observations
for each row execute function zk.reject_ml_challenger_mutation();

create table zk.ml_predictions (
    fit_id text not null references zk.ml_challenger_fits(fit_id),
    security_id text not null,
    prediction_at timestamptz not null,
    raw_score numeric not null,
    created_at timestamptz not null default now(),
    primary key (fit_id, security_id, prediction_at),
    constraint ml_prediction_score_chk check (
        raw_score not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
    )
);

create function zk.validate_ml_prediction()
returns trigger language plpgsql as $fn$
declare
    fit_time timestamptz;
begin
    select fit_at into fit_time from zk.ml_challenger_fits where fit_id = new.fit_id;
    if new.prediction_at <= fit_time then
        raise exception 'prediction must strictly follow model fit';
    end if;
    return new;
end;
$fn$;

create trigger ml_predictions_validate_trg
before insert on zk.ml_predictions
for each row execute function zk.validate_ml_prediction();

create trigger ml_predictions_immutable_trg
before update or delete on zk.ml_predictions
for each row execute function zk.reject_ml_challenger_mutation();
