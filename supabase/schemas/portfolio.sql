-- Zincir Kıran — Portfolio Engine schema v0.1
-- Long-only construction consumes Alpha + Confidence and never mutates them.

create table zk.portfolio_specs (
    specification_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    base_alpha_specification_id text not null,
    base_alpha_definition_version text not null,
    confidence_specification_id text not null,
    confidence_definition_version text not null,
    universe_rule_version text not null,
    hypothesis text not null,
    success_criteria text not null,
    preregistered_at timestamptz not null,
    selection_rule text not null,
    sizing_rule text not null,
    rebalance_rule_id text not null,
    target_position_count integer not null,
    minimum_position_count integer not null,
    minimum_alpha_value numeric not null,
    target_invested_weight numeric not null,
    max_single_name_weight numeric not null,
    max_sector_weight numeric not null,
    max_participation_rate numeric not null,
    execution_days integer not null,
    max_liquidity_age_days integer not null,
    maximum_one_way_turnover numeric not null,
    stage text not null default 'CANDIDATE',
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint portfolio_specs_alpha_fk
        foreign key (base_alpha_specification_id, base_alpha_definition_version)
        references zk.alpha_aggregation_specs(specification_id, definition_version),
    constraint portfolio_specs_confidence_fk
        foreign key (confidence_specification_id, confidence_definition_version)
        references zk.confidence_specs(specification_id, definition_version),
    constraint portfolio_specs_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint portfolio_specs_selection_chk
        check (selection_rule = 'TOP_ALPHA'),
    constraint portfolio_specs_sizing_chk
        check (sizing_rule in ('EQUAL_WEIGHT', 'POSITIVE_ALPHA_PROPORTIONAL')),
    constraint portfolio_specs_counts_chk
        check (
            target_position_count >= 1
            and minimum_position_count >= 1
            and minimum_position_count <= target_position_count
        ),
    constraint portfolio_specs_weights_chk
        check (
            target_invested_weight > 0 and target_invested_weight <= 1
            and max_single_name_weight > 0 and max_single_name_weight <= 1
            and max_sector_weight > 0 and max_sector_weight <= 1
            and max_participation_rate > 0 and max_participation_rate <= 1
            and maximum_one_way_turnover >= 0
        ),
    constraint portfolio_specs_execution_chk
        check (execution_days >= 1 and max_liquidity_age_days >= 0),
    constraint portfolio_specs_finite_chk
        check (
            minimum_alpha_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and target_invested_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and max_single_name_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and max_sector_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and max_participation_rate not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and maximum_one_way_turnover not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint portfolio_specs_candidate_only_chk
        check (stage = 'CANDIDATE'),
    constraint portfolio_specs_text_chk
        check (
            length(trim(specification_id)) > 0
            and length(trim(definition_version)) > 0
            and length(trim(universe_rule_version)) > 0
            and length(trim(hypothesis)) > 0
            and length(trim(success_criteria)) > 0
            and length(trim(rebalance_rule_id)) > 0
        )
);

create function zk.reject_portfolio_mutation()
returns trigger
language plpgsql
as $fn$
begin
    raise exception 'portfolio records are append-only';
end;
$fn$;

create function zk.validate_portfolio_spec()
returns trigger
language plpgsql
as $fn$
declare
    alpha_horizon integer;
    confidence_horizon integer;
    confidence_alpha_id text;
    confidence_alpha_version text;
begin
    select horizon_days into alpha_horizon
      from zk.alpha_aggregation_specs
     where specification_id = new.base_alpha_specification_id
       and definition_version = new.base_alpha_definition_version;

    select horizon_days, base_alpha_specification_id, base_alpha_definition_version
      into confidence_horizon, confidence_alpha_id, confidence_alpha_version
      from zk.confidence_specs
     where specification_id = new.confidence_specification_id
       and definition_version = new.confidence_definition_version;

    if alpha_horizon <> new.horizon_days or confidence_horizon <> new.horizon_days then
        raise exception 'portfolio horizon does not match Alpha/Confidence';
    end if;
    if (
        confidence_alpha_id <> new.base_alpha_specification_id
        or confidence_alpha_version <> new.base_alpha_definition_version
    ) then
        raise exception 'portfolio Confidence does not reference the same base Alpha';
    end if;
    return new;
end;
$fn$;

create trigger portfolio_specs_validate_trg
before insert on zk.portfolio_specs
for each row execute function zk.validate_portfolio_spec();

create trigger portfolio_specs_immutable_trg
before update or delete on zk.portfolio_specs
for each row execute function zk.reject_portfolio_mutation();

create table zk.portfolio_runs (
    portfolio_run_id text primary key,
    specification_id text not null,
    definition_version text not null,
    prediction_timestamp timestamptz not null,
    portfolio_notional numeric not null,
    status text not null,
    cash_weight numeric not null,
    one_way_turnover numeric not null,
    gross_turnover numeric not null,
    total_estimated_cost numeric not null,
    created_at timestamptz not null default now(),
    constraint portfolio_runs_spec_fk
        foreign key (specification_id, definition_version)
        references zk.portfolio_specs(specification_id, definition_version),
    constraint portfolio_runs_status_chk
        check (status in (
            'CONSTRUCTED',
            'INFEASIBLE_INSUFFICIENT_ELIGIBLE',
            'INFEASIBLE_CONSTRAINTS',
            'INFEASIBLE_LIQUIDITY',
            'INFEASIBLE_TURNOVER'
        )),
    constraint portfolio_runs_numeric_chk
        check (
            portfolio_notional > 0
            and cash_weight >= 0 and cash_weight <= 1
            and one_way_turnover >= 0
            and gross_turnover >= 0
            and total_estimated_cost >= 0
            and portfolio_notional not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and cash_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and one_way_turnover not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and gross_turnover not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and total_estimated_cost not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint portfolio_runs_turnover_chk
        check (gross_turnover = 2 * one_way_turnover)
);

create function zk.validate_portfolio_run()
returns trigger
language plpgsql
as $fn$
declare
    preregistered_time timestamptz;
begin
    select preregistered_at into preregistered_time
      from zk.portfolio_specs
     where specification_id = new.specification_id
       and definition_version = new.definition_version;

    if preregistered_time > new.prediction_timestamp then
        raise exception 'portfolio specification was not preregistered by prediction time';
    end if;
    return new;
end;
$fn$;

create trigger portfolio_runs_validate_trg
before insert on zk.portfolio_runs
for each row execute function zk.validate_portfolio_run();

create trigger portfolio_runs_immutable_trg
before update or delete on zk.portfolio_runs
for each row execute function zk.reject_portfolio_mutation();

create table zk.portfolio_run_candidates (
    portfolio_run_id text not null references zk.portfolio_runs(portfolio_run_id),
    security_id uuid not null references zk.securities(security_id),
    sector_id text not null,
    alpha_run_id text not null references zk.alpha_runs(alpha_run_id),
    confidence_run_id text not null references zk.confidence_runs(confidence_run_id),
    alpha_value numeric,
    confidence_score numeric,
    eligible boolean not null,
    created_at timestamptz not null default now(),
    primary key (portfolio_run_id, security_id),
    constraint portfolio_candidate_sector_chk
        check (length(trim(sector_id)) > 0),
    constraint portfolio_candidate_values_chk
        check (
            (alpha_value is null or alpha_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric))
            and (confidence_score is null or confidence_score not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric))
        )
);

create function zk.validate_portfolio_candidate()
returns trigger
language plpgsql
as $fn$
declare
    alpha_security uuid;
    alpha_spec_id text;
    alpha_spec_version text;
    alpha_status text;
    alpha_db_value numeric;
    confidence_spec_id text;
    confidence_spec_version text;
    confidence_alpha_run text;
    confidence_decision text;
    confidence_db_score numeric;
    expected_alpha_id text;
    expected_alpha_version text;
    expected_confidence_id text;
    expected_confidence_version text;
    minimum_alpha numeric;
    expected_eligible boolean;
begin
    select s.base_alpha_specification_id, s.base_alpha_definition_version,
           s.confidence_specification_id, s.confidence_definition_version,
           s.minimum_alpha_value
      into expected_alpha_id, expected_alpha_version,
           expected_confidence_id, expected_confidence_version,
           minimum_alpha
      from zk.portfolio_runs r
      join zk.portfolio_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where r.portfolio_run_id = new.portfolio_run_id;

    select security_id, specification_id, definition_version, status, alpha_value
      into alpha_security, alpha_spec_id, alpha_spec_version, alpha_status, alpha_db_value
      from zk.alpha_runs
     where alpha_run_id = new.alpha_run_id;

    select specification_id, definition_version, alpha_run_id, decision, confidence_score
      into confidence_spec_id, confidence_spec_version, confidence_alpha_run,
           confidence_decision, confidence_db_score
      from zk.confidence_runs
     where confidence_run_id = new.confidence_run_id;

    if alpha_security <> new.security_id then
        raise exception 'portfolio candidate Alpha security mismatch';
    end if;
    if alpha_spec_id <> expected_alpha_id or alpha_spec_version <> expected_alpha_version then
        raise exception 'portfolio candidate Alpha specification mismatch';
    end if;
    if (
        confidence_spec_id <> expected_confidence_id
        or confidence_spec_version <> expected_confidence_version
    ) then
        raise exception 'portfolio candidate Confidence specification mismatch';
    end if;
    if confidence_alpha_run <> new.alpha_run_id then
        raise exception 'portfolio candidate Confidence does not reference candidate Alpha run';
    end if;
    if new.alpha_value is distinct from alpha_db_value then
        raise exception 'portfolio candidate alpha_value mutation detected';
    end if;
    if new.confidence_score is distinct from confidence_db_score then
        raise exception 'portfolio candidate confidence_score mutation detected';
    end if;

    expected_eligible := (
        alpha_status = 'SCORED'
        and confidence_decision = 'SIGNAL_ELIGIBLE'
        and alpha_db_value is not null
        and alpha_db_value >= minimum_alpha
    );
    if expected_eligible and confidence_db_score is null then
        raise exception 'eligible portfolio candidate requires Confidence score';
    end if;
    if new.eligible <> expected_eligible then
        raise exception 'portfolio candidate eligibility mismatch';
    end if;
    return new;
end;
$fn$;

create trigger portfolio_run_candidates_validate_trg
before insert on zk.portfolio_run_candidates
for each row execute function zk.validate_portfolio_candidate();

create trigger portfolio_run_candidates_immutable_trg
before update or delete on zk.portfolio_run_candidates
for each row execute function zk.reject_portfolio_mutation();

create table zk.portfolio_current_holdings (
    portfolio_run_id text not null references zk.portfolio_runs(portfolio_run_id),
    security_id uuid not null references zk.securities(security_id),
    weight numeric not null,
    created_at timestamptz not null default now(),
    primary key (portfolio_run_id, security_id),
    constraint portfolio_current_holding_weight_chk
        check (
            weight >= 0
            and weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        )
);

create trigger portfolio_current_holdings_immutable_trg
before update or delete on zk.portfolio_current_holdings
for each row execute function zk.reject_portfolio_mutation();

create table zk.portfolio_execution_evidence (
    portfolio_run_id text not null references zk.portfolio_runs(portfolio_run_id),
    security_id uuid not null references zk.securities(security_id),
    window_end timestamptz not null,
    available_at timestamptz not null,
    average_daily_notional numeric not null,
    commission_bps numeric not null,
    half_spread_bps numeric not null,
    slippage_bps numeric not null,
    market_impact_bps numeric not null,
    source_reference text not null,
    created_at timestamptz not null default now(),
    primary key (portfolio_run_id, security_id),
    constraint portfolio_execution_time_chk
        check (window_end <= available_at),
    constraint portfolio_execution_adv_chk
        check (
            average_daily_notional > 0
            and average_daily_notional not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint portfolio_execution_cost_chk
        check (
            commission_bps >= 0
            and half_spread_bps >= 0
            and slippage_bps >= 0
            and market_impact_bps >= 0
            and commission_bps not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and half_spread_bps not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and slippage_bps not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and market_impact_bps not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint portfolio_execution_source_chk
        check (length(trim(source_reference)) > 0)
);

create function zk.validate_portfolio_execution_evidence()
returns trigger
language plpgsql
as $fn$
declare
    prediction_time timestamptz;
begin
    select prediction_timestamp into prediction_time
      from zk.portfolio_runs
     where portfolio_run_id = new.portfolio_run_id;

    if new.window_end > prediction_time or new.available_at > prediction_time then
        raise exception 'future execution evidence cannot enter portfolio run';
    end if;
    return new;
end;
$fn$;

create trigger portfolio_execution_evidence_validate_trg
before insert on zk.portfolio_execution_evidence
for each row execute function zk.validate_portfolio_execution_evidence();

create trigger portfolio_execution_evidence_immutable_trg
before update or delete on zk.portfolio_execution_evidence
for each row execute function zk.reject_portfolio_mutation();

create table zk.portfolio_target_positions (
    portfolio_run_id text not null references zk.portfolio_runs(portfolio_run_id),
    security_id uuid not null references zk.securities(security_id),
    sector_id text not null,
    alpha_value numeric not null,
    confidence_score numeric not null,
    rank integer not null,
    target_weight numeric not null,
    created_at timestamptz not null default now(),
    primary key (portfolio_run_id, security_id),
    unique (portfolio_run_id, rank),
    constraint portfolio_target_rank_chk check (rank >= 1),
    constraint portfolio_target_weight_chk
        check (
            target_weight > 0
            and target_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        ),
    constraint portfolio_target_value_chk
        check (
            alpha_value not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and confidence_score not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        )
);

create function zk.validate_portfolio_target_position()
returns trigger
language plpgsql
as $fn$
declare
    candidate_sector text;
    candidate_alpha numeric;
    candidate_confidence numeric;
    candidate_eligible boolean;
    max_name numeric;
begin
    select c.sector_id, c.alpha_value, c.confidence_score, c.eligible,
           s.max_single_name_weight
      into candidate_sector, candidate_alpha, candidate_confidence,
           candidate_eligible, max_name
      from zk.portfolio_run_candidates c
      join zk.portfolio_runs r on r.portfolio_run_id = c.portfolio_run_id
      join zk.portfolio_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where c.portfolio_run_id = new.portfolio_run_id
       and c.security_id = new.security_id;

    if candidate_eligible is distinct from true then
        raise exception 'target position requires eligible portfolio candidate';
    end if;
    if new.sector_id <> candidate_sector then
        raise exception 'target position sector mismatch';
    end if;
    if new.alpha_value <> candidate_alpha or new.confidence_score <> candidate_confidence then
        raise exception 'target position Alpha/Confidence mutation detected';
    end if;
    if new.target_weight > max_name then
        raise exception 'target position exceeds max single-name weight';
    end if;
    return new;
end;
$fn$;

create trigger portfolio_target_positions_validate_trg
before insert on zk.portfolio_target_positions
for each row execute function zk.validate_portfolio_target_position();

create trigger portfolio_target_positions_immutable_trg
before update or delete on zk.portfolio_target_positions
for each row execute function zk.reject_portfolio_mutation();

create table zk.portfolio_orders (
    portfolio_run_id text not null references zk.portfolio_runs(portfolio_run_id),
    security_id uuid not null references zk.securities(security_id),
    side text not null,
    current_weight numeric not null,
    target_weight numeric not null,
    delta_weight numeric not null,
    trade_notional numeric not null,
    max_trade_notional numeric,
    commission_cost numeric not null,
    spread_cost numeric not null,
    slippage_cost numeric not null,
    market_impact_cost numeric not null,
    total_cost numeric not null,
    created_at timestamptz not null default now(),
    primary key (portfolio_run_id, security_id),
    constraint portfolio_orders_side_chk
        check (side in ('BUY', 'SELL', 'HOLD')),
    constraint portfolio_orders_nonnegative_chk
        check (
            current_weight >= 0 and target_weight >= 0
            and trade_notional >= 0
            and (max_trade_notional is null or max_trade_notional >= 0)
            and commission_cost >= 0 and spread_cost >= 0
            and slippage_cost >= 0 and market_impact_cost >= 0
            and total_cost >= 0
        ),
    constraint portfolio_orders_finite_chk
        check (
            current_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and target_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and delta_weight not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and trade_notional not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and (max_trade_notional is null or max_trade_notional not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric))
            and commission_cost not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and spread_cost not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and slippage_cost not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and market_impact_cost not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
            and total_cost not in ('NaN'::numeric, 'Infinity'::numeric, '-Infinity'::numeric)
        )
);

create function zk.validate_portfolio_order()
returns trigger
language plpgsql
as $fn$
declare
    run_notional numeric;
    prediction_time timestamptz;
    participation numeric;
    execution_day_count integer;
    max_age integer;
    expected_current numeric;
    expected_target numeric;
    expected_delta numeric;
    expected_side text;
    evidence_window_end timestamptz;
    adv numeric;
    commission_bps_value numeric;
    spread_bps_value numeric;
    slippage_bps_value numeric;
    impact_bps_value numeric;
    expected_trade numeric;
    expected_max_trade numeric;
    expected_commission numeric;
    expected_spread numeric;
    expected_slippage numeric;
    expected_impact numeric;
begin
    select r.portfolio_notional, r.prediction_timestamp,
           s.max_participation_rate, s.execution_days, s.max_liquidity_age_days
      into run_notional, prediction_time, participation, execution_day_count, max_age
      from zk.portfolio_runs r
      join zk.portfolio_specs s
        on s.specification_id = r.specification_id
       and s.definition_version = r.definition_version
     where r.portfolio_run_id = new.portfolio_run_id;

    select coalesce(weight, 0) into expected_current
      from zk.portfolio_current_holdings
     where portfolio_run_id = new.portfolio_run_id
       and security_id = new.security_id;
    if not found then expected_current := 0; end if;

    select coalesce(target_weight, 0) into expected_target
      from zk.portfolio_target_positions
     where portfolio_run_id = new.portfolio_run_id
       and security_id = new.security_id;
    if not found then expected_target := 0; end if;

    expected_delta := expected_target - expected_current;
    expected_side := case
        when expected_delta > 0 then 'BUY'
        when expected_delta < 0 then 'SELL'
        else 'HOLD'
    end;

    if (
        new.current_weight <> expected_current
        or new.target_weight <> expected_target
        or new.delta_weight <> expected_delta
        or new.side <> expected_side
    ) then
        raise exception 'portfolio order weights/side mismatch';
    end if;

    if expected_side = 'HOLD' then
        if (
            new.trade_notional <> 0
            or new.max_trade_notional is not null
            or new.commission_cost <> 0
            or new.spread_cost <> 0
            or new.slippage_cost <> 0
            or new.market_impact_cost <> 0
            or new.total_cost <> 0
        ) then
            raise exception 'HOLD order must carry zero trade and cost';
        end if;
        return new;
    end if;

    select window_end, average_daily_notional, commission_bps,
           half_spread_bps, slippage_bps, market_impact_bps
      into evidence_window_end, adv, commission_bps_value,
           spread_bps_value, slippage_bps_value, impact_bps_value
      from zk.portfolio_execution_evidence
     where portfolio_run_id = new.portfolio_run_id
       and security_id = new.security_id;

    if not found then
        raise exception 'trade order requires execution evidence';
    end if;
    if extract(epoch from (prediction_time - evidence_window_end)) / 86400 > max_age then
        raise exception 'trade order cannot use stale execution evidence';
    end if;

    expected_trade := abs(expected_delta) * run_notional;
    expected_max_trade := adv * participation * execution_day_count;
    if expected_trade > expected_max_trade then
        raise exception 'trade order exceeds capacity';
    end if;

    expected_commission := expected_trade * commission_bps_value / 10000;
    expected_spread := expected_trade * spread_bps_value / 10000;
    expected_slippage := expected_trade * slippage_bps_value / 10000;
    expected_impact := expected_trade * impact_bps_value / 10000;

    if new.trade_notional <> expected_trade or new.max_trade_notional <> expected_max_trade then
        raise exception 'portfolio order trade/capacity arithmetic mismatch';
    end if;
    if (
        new.commission_cost <> expected_commission
        or new.spread_cost <> expected_spread
        or new.slippage_cost <> expected_slippage
        or new.market_impact_cost <> expected_impact
        or new.total_cost <> (
            expected_commission + expected_spread + expected_slippage + expected_impact
        )
    ) then
        raise exception 'portfolio order cost arithmetic mismatch';
    end if;
    return new;
end;
$fn$;

create trigger portfolio_orders_validate_trg
before insert on zk.portfolio_orders
for each row execute function zk.validate_portfolio_order();

create trigger portfolio_orders_immutable_trg
before update or delete on zk.portfolio_orders
for each row execute function zk.reject_portfolio_mutation();

create table zk.portfolio_infeasibility_reasons (
    portfolio_reason_id bigint generated always as identity primary key,
    portfolio_run_id text not null references zk.portfolio_runs(portfolio_run_id),
    reason_code text not null,
    security_id uuid references zk.securities(security_id),
    created_at timestamptz not null default now(),
    constraint portfolio_reason_code_chk
        check (reason_code in (
            'INSUFFICIENT_ELIGIBLE_SECURITIES',
            'WEIGHT_OR_SECTOR_CAPS_INFEASIBLE',
            'MISSING_EXECUTION_EVIDENCE',
            'STALE_EXECUTION_EVIDENCE',
            'CAPACITY_EXCEEDED',
            'MAXIMUM_ONE_WAY_TURNOVER_EXCEEDED'
        )),
    constraint portfolio_reason_shape_chk
        check (
            (
                reason_code in (
                    'MISSING_EXECUTION_EVIDENCE',
                    'STALE_EXECUTION_EVIDENCE',
                    'CAPACITY_EXCEEDED'
                )
                and security_id is not null
            )
            or (
                reason_code not in (
                    'MISSING_EXECUTION_EVIDENCE',
                    'STALE_EXECUTION_EVIDENCE',
                    'CAPACITY_EXCEEDED'
                )
                and security_id is null
            )
        )
);

create unique index portfolio_reason_identity_uidx
    on zk.portfolio_infeasibility_reasons(
        portfolio_run_id,
        reason_code,
        coalesce(security_id::text, '')
    );

create trigger portfolio_infeasibility_reasons_immutable_trg
before update or delete on zk.portfolio_infeasibility_reasons
for each row execute function zk.reject_portfolio_mutation();

create function zk.audit_portfolio_run_complete()
returns trigger
language plpgsql
as $fn$
declare
    run_record zk.portfolio_runs%rowtype;
    spec_record zk.portfolio_specs%rowtype;
    current_weight_sum numeric;
    eligible_count integer;
    expected_selected_count integer;
    target_count integer;
    target_weight_sum numeric;
    sector_violation_count integer;
    name_violation_count integer;
    sizing_violation_count integer;
    gross_turnover_expected numeric;
    one_way_turnover_expected numeric;
    cash_expected numeric;
    order_cost_expected numeric;
    liquidity_failure_count integer;
    expected_status text;
    reason_count integer;
    required_order_count integer;
    actual_order_count integer;
begin
    select * into run_record
      from zk.portfolio_runs
     where portfolio_run_id = new.portfolio_run_id;

    select * into spec_record
      from zk.portfolio_specs
     where specification_id = run_record.specification_id
       and definition_version = run_record.definition_version;

    select coalesce(sum(weight), 0) into current_weight_sum
      from zk.portfolio_current_holdings
     where portfolio_run_id = run_record.portfolio_run_id;
    if current_weight_sum > 1 then
        raise exception 'current portfolio holding weights exceed 1';
    end if;

    select count(*) into eligible_count
      from zk.portfolio_run_candidates
     where portfolio_run_id = run_record.portfolio_run_id
       and eligible;

    if eligible_count < spec_record.minimum_position_count then
        expected_status := 'INFEASIBLE_INSUFFICIENT_ELIGIBLE';
        expected_selected_count := 0;
    else
        expected_selected_count := least(spec_record.target_position_count, eligible_count);

        with ranked as (
            select c.*,
                   row_number() over (
                       order by c.alpha_value desc, c.security_id::text
                   ) as expected_rank
              from zk.portfolio_run_candidates c
             where c.portfolio_run_id = run_record.portfolio_run_id
               and c.eligible
        ),
        selected as (
            select *
              from ranked
             where expected_rank <= expected_selected_count
        ),
        expected as (
            select s.*,
                   case
                       when spec_record.sizing_rule = 'EQUAL_WEIGHT'
                           then spec_record.target_invested_weight / expected_selected_count
                       else
                           spec_record.target_invested_weight
                           * s.alpha_value
                           / nullif(sum(s.alpha_value) over (), 0)
                   end as expected_weight
              from selected s
        )
        select
            count(*) filter (
                where expected_weight > spec_record.max_single_name_weight
            ),
            count(*) filter (
                where spec_record.sizing_rule = 'POSITIVE_ALPHA_PROPORTIONAL'
                  and alpha_value <= 0
            )
          into name_violation_count, sizing_violation_count
          from expected;

        with ranked as (
            select c.*,
                   row_number() over (
                       order by c.alpha_value desc, c.security_id::text
                   ) as expected_rank
              from zk.portfolio_run_candidates c
             where c.portfolio_run_id = run_record.portfolio_run_id
               and c.eligible
        ),
        selected as (
            select *
              from ranked
             where expected_rank <= expected_selected_count
        ),
        expected as (
            select s.*,
                   case
                       when spec_record.sizing_rule = 'EQUAL_WEIGHT'
                           then spec_record.target_invested_weight / expected_selected_count
                       else
                           spec_record.target_invested_weight
                           * s.alpha_value
                           / nullif(sum(s.alpha_value) over (), 0)
                   end as expected_weight
              from selected s
        ),
        sector_totals as (
            select sector_id, sum(expected_weight) as sector_weight
              from expected
             group by sector_id
        )
        select count(*) into sector_violation_count
          from sector_totals
         where sector_weight > spec_record.max_sector_weight;

        if (
            coalesce(name_violation_count, 0) > 0
            or coalesce(sector_violation_count, 0) > 0
            or coalesce(sizing_violation_count, 0) > 0
        ) then
            expected_status := 'INFEASIBLE_CONSTRAINTS';
        end if;
    end if;

    select count(*), coalesce(sum(target_weight), 0)
      into target_count, target_weight_sum
      from zk.portfolio_target_positions
     where portfolio_run_id = run_record.portfolio_run_id;

    if expected_status in (
        'INFEASIBLE_INSUFFICIENT_ELIGIBLE',
        'INFEASIBLE_CONSTRAINTS'
    ) then
        if target_count <> 0 then
            raise exception 'infeasible pre-trade portfolio cannot contain target positions';
        end if;
        if (
            run_record.cash_weight <> 1
            or run_record.one_way_turnover <> 0
            or run_record.gross_turnover <> 0
            or run_record.total_estimated_cost <> 0
        ) then
            raise exception 'pre-trade infeasible portfolio must have zero turnover/cost';
        end if;
    else
        if target_count <> expected_selected_count then
            raise exception 'portfolio target position count mismatch';
        end if;
        if target_weight_sum <> spec_record.target_invested_weight then
            raise exception 'portfolio target invested weight mismatch';
        end if;

        if exists (
            with ranked as (
                select c.*,
                       row_number() over (
                           order by c.alpha_value desc, c.security_id::text
                       ) as expected_rank
                  from zk.portfolio_run_candidates c
                 where c.portfolio_run_id = run_record.portfolio_run_id
                   and c.eligible
            ),
            selected as (
                select *
                  from ranked
                 where expected_rank <= expected_selected_count
            ),
            expected as (
                select s.*,
                       case
                           when spec_record.sizing_rule = 'EQUAL_WEIGHT'
                               then spec_record.target_invested_weight / expected_selected_count
                           else
                               spec_record.target_invested_weight
                               * s.alpha_value
                               / nullif(sum(s.alpha_value) over (), 0)
                       end as expected_weight
                  from selected s
            )
            select 1
              from expected e
              full join zk.portfolio_target_positions t
                on t.portfolio_run_id = run_record.portfolio_run_id
               and t.security_id = e.security_id
             where e.security_id is null
                or t.security_id is null
                or t.rank <> e.expected_rank
                or t.target_weight <> e.expected_weight
                or t.sector_id <> e.sector_id
                or t.alpha_value <> e.alpha_value
                or t.confidence_score <> e.confidence_score
        ) then
            raise exception 'portfolio target selection/sizing mismatch';
        end if;

        if exists (
            select 1
              from (
                  select sector_id, sum(target_weight) as sector_weight
                    from zk.portfolio_target_positions
                   where portfolio_run_id = run_record.portfolio_run_id
                   group by sector_id
              ) s
             where s.sector_weight > spec_record.max_sector_weight
        ) then
            raise exception 'portfolio sector cap violated';
        end if;

        with union_ids as (
            select security_id
              from zk.portfolio_current_holdings
             where portfolio_run_id = run_record.portfolio_run_id
            union
            select security_id
              from zk.portfolio_target_positions
             where portfolio_run_id = run_record.portfolio_run_id
        ),
        deltas as (
            select u.security_id,
                   coalesce(c.weight, 0) as current_weight,
                   coalesce(t.target_weight, 0) as target_weight,
                   coalesce(t.target_weight, 0) - coalesce(c.weight, 0) as delta_weight
              from union_ids u
              left join zk.portfolio_current_holdings c
                on c.portfolio_run_id = run_record.portfolio_run_id
               and c.security_id = u.security_id
              left join zk.portfolio_target_positions t
                on t.portfolio_run_id = run_record.portfolio_run_id
               and t.security_id = u.security_id
        )
        select coalesce(sum(abs(delta_weight)), 0)
          into gross_turnover_expected
          from deltas;

        one_way_turnover_expected := gross_turnover_expected / 2;
        cash_expected := 1 - target_weight_sum;

        if (
            run_record.gross_turnover <> gross_turnover_expected
            or run_record.one_way_turnover <> one_way_turnover_expected
            or run_record.cash_weight <> cash_expected
        ) then
            raise exception 'portfolio turnover/cash arithmetic mismatch';
        end if;

        with union_ids as (
            select security_id
              from zk.portfolio_current_holdings
             where portfolio_run_id = run_record.portfolio_run_id
            union
            select security_id
              from zk.portfolio_target_positions
             where portfolio_run_id = run_record.portfolio_run_id
        ),
        deltas as (
            select u.security_id,
                   coalesce(t.target_weight, 0) - coalesce(c.weight, 0) as delta_weight
              from union_ids u
              left join zk.portfolio_current_holdings c
                on c.portfolio_run_id = run_record.portfolio_run_id
               and c.security_id = u.security_id
              left join zk.portfolio_target_positions t
                on t.portfolio_run_id = run_record.portfolio_run_id
               and t.security_id = u.security_id
        ),
        failures as (
            select d.security_id,
                   case
                       when e.security_id is null then 'MISSING_EXECUTION_EVIDENCE'
                       when extract(
                           epoch from (run_record.prediction_timestamp - e.window_end)
                       ) / 86400 > spec_record.max_liquidity_age_days
                           then 'STALE_EXECUTION_EVIDENCE'
                       when (
                           abs(d.delta_weight) * run_record.portfolio_notional
                           > e.average_daily_notional
                             * spec_record.max_participation_rate
                             * spec_record.execution_days
                       ) then 'CAPACITY_EXCEEDED'
                       else null
                   end as reason_code
              from deltas d
              left join zk.portfolio_execution_evidence e
                on e.portfolio_run_id = run_record.portfolio_run_id
               and e.security_id = d.security_id
             where d.delta_weight <> 0
        )
        select count(*) into liquidity_failure_count
          from failures
         where reason_code is not null;

        if liquidity_failure_count > 0 then
            expected_status := 'INFEASIBLE_LIQUIDITY';

            if exists (
                with union_ids as (
                    select security_id
                      from zk.portfolio_current_holdings
                     where portfolio_run_id = run_record.portfolio_run_id
                    union
                    select security_id
                      from zk.portfolio_target_positions
                     where portfolio_run_id = run_record.portfolio_run_id
                ),
                deltas as (
                    select u.security_id,
                           coalesce(t.target_weight, 0) - coalesce(c.weight, 0) as delta_weight
                      from union_ids u
                      left join zk.portfolio_current_holdings c
                        on c.portfolio_run_id = run_record.portfolio_run_id
                       and c.security_id = u.security_id
                      left join zk.portfolio_target_positions t
                        on t.portfolio_run_id = run_record.portfolio_run_id
                       and t.security_id = u.security_id
                ),
                failures as (
                    select d.security_id,
                           case
                               when e.security_id is null then 'MISSING_EXECUTION_EVIDENCE'
                               when extract(
                                   epoch from (run_record.prediction_timestamp - e.window_end)
                               ) / 86400 > spec_record.max_liquidity_age_days
                                   then 'STALE_EXECUTION_EVIDENCE'
                               when (
                                   abs(d.delta_weight) * run_record.portfolio_notional
                                   > e.average_daily_notional
                                     * spec_record.max_participation_rate
                                     * spec_record.execution_days
                               ) then 'CAPACITY_EXCEEDED'
                               else null
                           end as reason_code
                      from deltas d
                      left join zk.portfolio_execution_evidence e
                        on e.portfolio_run_id = run_record.portfolio_run_id
                       and e.security_id = d.security_id
                     where d.delta_weight <> 0
                )
                select 1
                  from failures f
                 where f.reason_code is not null
                   and not exists (
                       select 1
                         from zk.portfolio_infeasibility_reasons r
                        where r.portfolio_run_id = run_record.portfolio_run_id
                          and r.security_id = f.security_id
                          and r.reason_code = f.reason_code
                   )
            ) then
                raise exception 'portfolio liquidity infeasibility reasons incomplete';
            end if;
        elsif one_way_turnover_expected > spec_record.maximum_one_way_turnover then
            expected_status := 'INFEASIBLE_TURNOVER';
        else
            expected_status := 'CONSTRUCTED';
        end if;

        select count(*) into required_order_count
          from (
              with union_ids as (
                  select security_id
                    from zk.portfolio_current_holdings
                   where portfolio_run_id = run_record.portfolio_run_id
                  union
                  select security_id
                    from zk.portfolio_target_positions
                   where portfolio_run_id = run_record.portfolio_run_id
              ),
              deltas as (
                  select u.security_id,
                         coalesce(t.target_weight, 0) - coalesce(c.weight, 0) as delta_weight
                    from union_ids u
                    left join zk.portfolio_current_holdings c
                      on c.portfolio_run_id = run_record.portfolio_run_id
                     and c.security_id = u.security_id
                    left join zk.portfolio_target_positions t
                      on t.portfolio_run_id = run_record.portfolio_run_id
                     and t.security_id = u.security_id
              )
              select d.security_id
                from deltas d
                left join zk.portfolio_infeasibility_reasons r
                  on r.portfolio_run_id = run_record.portfolio_run_id
                 and r.security_id = d.security_id
                 and r.reason_code in (
                     'MISSING_EXECUTION_EVIDENCE',
                     'STALE_EXECUTION_EVIDENCE',
                     'CAPACITY_EXCEEDED'
                 )
               where r.security_id is null
          ) q;

        select count(*) into actual_order_count
          from zk.portfolio_orders
         where portfolio_run_id = run_record.portfolio_run_id;

        if actual_order_count <> required_order_count then
            raise exception 'portfolio order coverage mismatch';
        end if;

        select coalesce(sum(total_cost), 0) into order_cost_expected
          from zk.portfolio_orders
         where portfolio_run_id = run_record.portfolio_run_id;

        if run_record.total_estimated_cost <> order_cost_expected then
            raise exception 'portfolio total estimated cost mismatch';
        end if;
    end if;

    if run_record.status <> expected_status then
        raise exception 'portfolio run status does not match constraints/evidence';
    end if;

    select count(*) into reason_count
      from zk.portfolio_infeasibility_reasons
     where portfolio_run_id = run_record.portfolio_run_id;

    if expected_status = 'CONSTRUCTED' then
        if reason_count <> 0 then
            raise exception 'constructed portfolio cannot carry infeasibility reasons';
        end if;
    elsif expected_status = 'INFEASIBLE_INSUFFICIENT_ELIGIBLE' then
        if reason_count <> 1 or not exists (
            select 1 from zk.portfolio_infeasibility_reasons
             where portfolio_run_id = run_record.portfolio_run_id
               and reason_code = 'INSUFFICIENT_ELIGIBLE_SECURITIES'
               and security_id is null
        ) then
            raise exception 'insufficient-eligible portfolio reason mismatch';
        end if;
    elsif expected_status = 'INFEASIBLE_CONSTRAINTS' then
        if reason_count <> 1 or not exists (
            select 1 from zk.portfolio_infeasibility_reasons
             where portfolio_run_id = run_record.portfolio_run_id
               and reason_code = 'WEIGHT_OR_SECTOR_CAPS_INFEASIBLE'
               and security_id is null
        ) then
            raise exception 'constraint-infeasible portfolio reason mismatch';
        end if;
    elsif expected_status = 'INFEASIBLE_TURNOVER' then
        if reason_count <> 1 or not exists (
            select 1 from zk.portfolio_infeasibility_reasons
             where portfolio_run_id = run_record.portfolio_run_id
               and reason_code = 'MAXIMUM_ONE_WAY_TURNOVER_EXCEEDED'
               and security_id is null
        ) then
            raise exception 'turnover-infeasible portfolio reason mismatch';
        end if;
    else
        if reason_count <> liquidity_failure_count then
            raise exception 'liquidity-infeasible portfolio reason count mismatch';
        end if;
    end if;

    return new;
end;
$fn$;

create constraint trigger portfolio_runs_complete_audit_trg
after insert on zk.portfolio_runs
deferrable initially deferred
for each row execute function zk.audit_portfolio_run_complete();

create index portfolio_candidates_alpha_idx
    on zk.portfolio_run_candidates(portfolio_run_id, eligible, alpha_value desc);

create index portfolio_execution_evidence_time_idx
    on zk.portfolio_execution_evidence(portfolio_run_id, security_id, available_at desc);
