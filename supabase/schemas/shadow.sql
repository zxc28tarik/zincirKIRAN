-- Zincir Kıran — Live Shadow Mode schema v0.1
-- Immutable live evidence only. No order execution and no automatic production promotion.

create table zk.shadow_protocols (
    protocol_id text not null,
    definition_version text not null,
    universe_rule_version text not null,
    alpha_specification_id text not null,
    alpha_definition_version text not null,
    confidence_specification_id text not null,
    confidence_definition_version text not null,
    ml_challenger_id text,
    ml_definition_version text,
    preregistered_at timestamptz not null,
    created_at timestamptz not null default now(),
    primary key (protocol_id, definition_version),
    constraint shadow_protocol_ml_pair_chk check (
        (ml_challenger_id is null and ml_definition_version is null)
        or (
            ml_challenger_id is not null
            and ml_definition_version is not null
            and length(trim(ml_challenger_id)) > 0
            and length(trim(ml_definition_version)) > 0
        )
    ),
    constraint shadow_protocol_text_chk check (
        length(trim(protocol_id)) > 0
        and length(trim(definition_version)) > 0
        and length(trim(universe_rule_version)) > 0
        and length(trim(alpha_specification_id)) > 0
        and length(trim(alpha_definition_version)) > 0
        and length(trim(confidence_specification_id)) > 0
        and length(trim(confidence_definition_version)) > 0
    )
);

create function zk.reject_shadow_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'shadow records are immutable';
end;
$fn$;

create trigger shadow_protocols_immutable_trg
before update or delete on zk.shadow_protocols
for each row execute function zk.reject_shadow_mutation();

create table zk.shadow_protocol_horizons (
    protocol_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    created_at timestamptz not null default now(),
    primary key (protocol_id, definition_version, horizon_days),
    foreign key (protocol_id, definition_version)
        references zk.shadow_protocols(protocol_id, definition_version),
    constraint shadow_horizon_chk check (horizon_days in (20, 60, 120, 252))
);

create trigger shadow_protocol_horizons_immutable_trg
before update or delete on zk.shadow_protocol_horizons
for each row execute function zk.reject_shadow_mutation();

create table zk.shadow_runs (
    shadow_run_id text primary key,
    protocol_id text not null,
    definition_version text not null,
    as_of timestamptz not null,
    executed_at timestamptz not null,
    data_snapshot_id text not null,
    universe_snapshot_id text not null,
    input_receipt_hash text not null,
    output_receipt_hash text not null,
    created_at timestamptz not null default now(),
    foreign key (protocol_id, definition_version)
        references zk.shadow_protocols(protocol_id, definition_version),
    constraint shadow_runs_time_chk check (executed_at >= as_of),
    constraint shadow_runs_text_chk check (
        length(trim(shadow_run_id)) > 0
        and length(trim(data_snapshot_id)) > 0
        and length(trim(universe_snapshot_id)) > 0
        and length(trim(input_receipt_hash)) > 0
        and length(trim(output_receipt_hash)) > 0
    )
);

create function zk.validate_shadow_run()
returns trigger language plpgsql as $fn$
declare
    prereg timestamptz;
begin
    select preregistered_at into prereg
      from zk.shadow_protocols
     where protocol_id = new.protocol_id
       and definition_version = new.definition_version;

    if new.as_of < prereg then
        raise exception 'shadow run cannot predate protocol preregistration';
    end if;

    return new;
end;
$fn$;

create trigger shadow_runs_validate_trg
before insert on zk.shadow_runs
for each row execute function zk.validate_shadow_run();

create trigger shadow_runs_immutable_trg
before update or delete on zk.shadow_runs
for each row execute function zk.reject_shadow_mutation();

create table zk.shadow_input_provenance (
    shadow_run_id text not null references zk.shadow_runs(shadow_run_id),
    provenance_key text not null,
    provenance_value text not null,
    created_at timestamptz not null default now(),
    primary key (shadow_run_id, provenance_key),
    constraint shadow_input_provenance_text_chk check (
        length(trim(provenance_key)) > 0
        and length(trim(provenance_value)) > 0
    )
);

create trigger shadow_input_provenance_immutable_trg
before update or delete on zk.shadow_input_provenance
for each row execute function zk.reject_shadow_mutation();

create table zk.shadow_security_decisions (
    shadow_run_id text not null references zk.shadow_runs(shadow_run_id),
    security_id text not null,
    decision text not null,
    alpha_score numeric,
    confidence_score numeric,
    ml_score numeric,
    portfolio_target_weight numeric,
    created_at timestamptz not null default now(),
    primary key (shadow_run_id, security_id),
    constraint shadow_decision_chk check (
        decision in ('SIGNAL_ELIGIBLE', 'NO_SIGNAL', 'ABSTAIN')
    ),
    constraint shadow_security_text_chk check (length(trim(security_id)) > 0),
    constraint shadow_numeric_chk check (
        (alpha_score is null or alpha_score not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric))
        and (confidence_score is null or confidence_score not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric))
        and (ml_score is null or ml_score not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric))
        and (
            portfolio_target_weight is null
            or (
                portfolio_target_weight >= 0
                and portfolio_target_weight not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
            )
        )
    ),
    constraint shadow_no_signal_weight_chk check (
        decision = 'SIGNAL_ELIGIBLE'
        or portfolio_target_weight is null
        or portfolio_target_weight = 0
    )
);

create trigger shadow_security_decisions_immutable_trg
before update or delete on zk.shadow_security_decisions
for each row execute function zk.reject_shadow_mutation();

create table zk.shadow_decision_reasons (
    shadow_run_id text not null,
    security_id text not null,
    reason_code text not null,
    created_at timestamptz not null default now(),
    primary key (shadow_run_id, security_id, reason_code),
    foreign key (shadow_run_id, security_id)
        references zk.shadow_security_decisions(shadow_run_id, security_id),
    constraint shadow_reason_text_chk check (length(trim(reason_code)) > 0)
);

create trigger shadow_decision_reasons_immutable_trg
before update or delete on zk.shadow_decision_reasons
for each row execute function zk.reject_shadow_mutation();

create table zk.shadow_realized_labels (
    shadow_run_id text not null,
    security_id text not null,
    horizon_days integer not null,
    label_available_at timestamptz not null,
    market_relative_total_return numeric not null,
    created_at timestamptz not null default now(),
    primary key (shadow_run_id, security_id, horizon_days),
    foreign key (shadow_run_id, security_id)
        references zk.shadow_security_decisions(shadow_run_id, security_id),
    constraint shadow_realized_horizon_chk check (horizon_days in (20,60,120,252)),
    constraint shadow_realized_value_chk check (
        market_relative_total_return not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
    )
);

create function zk.validate_shadow_realized_label()
returns trigger language plpgsql as $fn$
declare
    shadow_time timestamptz;
    protocol_key text;
    protocol_version text;
begin
    select r.as_of, r.protocol_id, r.definition_version
      into shadow_time, protocol_key, protocol_version
      from zk.shadow_runs r
     where r.shadow_run_id = new.shadow_run_id;

    if not exists (
        select 1 from zk.shadow_protocol_horizons h
         where h.protocol_id = protocol_key
           and h.definition_version = protocol_version
           and h.horizon_days = new.horizon_days
    ) then
        raise exception 'realized label horizon is not registered in shadow protocol';
    end if;

    if new.label_available_at < shadow_time + make_interval(days => new.horizon_days) then
        raise exception 'realized label is premature';
    end if;

    return new;
end;
$fn$;

create trigger shadow_realized_labels_validate_trg
before insert on zk.shadow_realized_labels
for each row execute function zk.validate_shadow_realized_label();

create trigger shadow_realized_labels_immutable_trg
before update or delete on zk.shadow_realized_labels
for each row execute function zk.reject_shadow_mutation();
