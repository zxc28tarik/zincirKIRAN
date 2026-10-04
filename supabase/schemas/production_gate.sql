-- Zincir Kıran — Production Decision Gate schema v0.1
-- Evidence gate only. No broker/order/deployment path.

create table zk.production_gate_specs (
    gate_id text not null,
    definition_version text not null,
    preregistered_at timestamptz not null,
    minimum_shadow_days integer not null,
    minimum_shadow_runs integer not null,
    minimum_realized_label_coverage numeric not null,
    minimum_mean_ic numeric not null,
    minimum_net_return_after_costs numeric not null,
    maximum_drawdown numeric not null,
    minimum_liquidity_fit numeric not null,
    require_replay_integrity boolean not null default true,
    require_pit_integrity boolean not null default true,
    require_cost_model boolean not null default true,
    require_capacity_evidence boolean not null default true,
    created_at timestamptz not null default now(),
    primary key (gate_id, definition_version),
    constraint production_gate_shadow_chk check (
        minimum_shadow_days >= 0 and minimum_shadow_runs >= 0
    ),
    constraint production_gate_coverage_chk check (
        minimum_realized_label_coverage between 0 and 1
        and minimum_liquidity_fit between 0 and 1
    ),
    constraint production_gate_drawdown_chk check (maximum_drawdown >= 0),
    constraint production_gate_text_chk check (
        length(trim(gate_id)) > 0 and length(trim(definition_version)) > 0
    )
);

create function zk.reject_production_gate_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'production gate records are immutable';
end;
$fn$;

create trigger production_gate_specs_immutable_trg
before update or delete on zk.production_gate_specs
for each row execute function zk.reject_production_gate_mutation();

create table zk.production_gate_evaluations (
    evaluation_id text primary key,
    gate_id text not null,
    definition_version text not null,
    evaluated_at timestamptz not null,
    tournament_run_id text,
    shadow_protocol_id text,
    shadow_days integer,
    shadow_runs integer,
    realized_label_coverage numeric,
    mean_ic numeric,
    net_return_after_costs numeric,
    max_drawdown numeric,
    liquidity_fit numeric,
    replay_integrity boolean,
    pit_integrity boolean,
    cost_model_present boolean,
    capacity_evidence_present boolean,
    decision text not null,
    review_required boolean not null,
    automatic_deployment boolean not null,
    created_at timestamptz not null default now(),
    foreign key (gate_id, definition_version)
        references zk.production_gate_specs(gate_id, definition_version),
    constraint production_gate_decision_chk check (
        decision in (
            'RESEARCH_ONLY',
            'EXTEND_SHADOW',
            'PRODUCTION_ELIGIBLE_REVIEW_REQUIRED',
            'REJECTED'
        )
    ),
    constraint production_gate_no_auto_deploy_chk check (automatic_deployment = false),
    constraint production_gate_review_chk check (review_required = true),
    constraint production_gate_eval_ranges_chk check (
        (shadow_days is null or shadow_days >= 0)
        and (shadow_runs is null or shadow_runs >= 0)
        and (
            realized_label_coverage is null
            or realized_label_coverage between 0 and 1
        )
        and (max_drawdown is null or max_drawdown >= 0)
        and (liquidity_fit is null or liquidity_fit between 0 and 1)
    )
);

create function zk.validate_production_gate_evaluation()
returns trigger language plpgsql as $fn$
declare
    prereg timestamptz;
begin
    select preregistered_at into prereg
      from zk.production_gate_specs
     where gate_id = new.gate_id
       and definition_version = new.definition_version;

    if new.evaluated_at <= prereg then
        raise exception 'production evaluation must follow preregistration';
    end if;

    if new.decision = 'PRODUCTION_ELIGIBLE_REVIEW_REQUIRED' then
        if new.tournament_run_id is null
           or new.shadow_protocol_id is null
           or new.shadow_days is null
           or new.shadow_runs is null
           or new.realized_label_coverage is null
           or new.mean_ic is null
           or new.net_return_after_costs is null
           or new.max_drawdown is null
           or new.liquidity_fit is null
           or new.replay_integrity is distinct from true
           or new.pit_integrity is distinct from true
           or new.cost_model_present is distinct from true
           or new.capacity_evidence_present is distinct from true then
            raise exception 'production eligibility cannot contain missing or failed required evidence';
        end if;
    end if;

    return new;
end;
$fn$;

create trigger production_gate_evaluations_validate_trg
before insert on zk.production_gate_evaluations
for each row execute function zk.validate_production_gate_evaluation();

create trigger production_gate_evaluations_immutable_trg
before update or delete on zk.production_gate_evaluations
for each row execute function zk.reject_production_gate_mutation();

create table zk.production_gate_failed_checks (
    evaluation_id text not null references zk.production_gate_evaluations(evaluation_id),
    check_code text not null,
    created_at timestamptz not null default now(),
    primary key (evaluation_id, check_code),
    constraint production_gate_failed_text_chk check (length(trim(check_code)) > 0)
);

create trigger production_gate_failed_checks_immutable_trg
before update or delete on zk.production_gate_failed_checks
for each row execute function zk.reject_production_gate_mutation();

create table zk.production_gate_missing_evidence (
    evaluation_id text not null references zk.production_gate_evaluations(evaluation_id),
    evidence_code text not null,
    created_at timestamptz not null default now(),
    primary key (evaluation_id, evidence_code),
    constraint production_gate_missing_text_chk check (length(trim(evidence_code)) > 0)
);

create trigger production_gate_missing_evidence_immutable_trg
before update or delete on zk.production_gate_missing_evidence
for each row execute function zk.reject_production_gate_mutation();
