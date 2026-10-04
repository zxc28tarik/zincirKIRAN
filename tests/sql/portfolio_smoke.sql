\set ON_ERROR_STOP on

insert into zk.companies (company_id, legal_name)
values ('74000000-0000-0000-0000-000000000001'::uuid, 'Portfolio Smoke Company');

insert into zk.securities (security_id, company_id)
values
    ('74000000-0000-0000-0000-000000000002'::uuid, '74000000-0000-0000-0000-000000000001'::uuid),
    ('74000000-0000-0000-0000-000000000003'::uuid, '74000000-0000-0000-0000-000000000001'::uuid),
    ('74000000-0000-0000-0000-000000000004'::uuid, '74000000-0000-0000-0000-000000000001'::uuid),
    ('74000000-0000-0000-0000-000000000005'::uuid, '74000000-0000-0000-0000-000000000001'::uuid);

insert into zk.alpha_aggregation_specs (
    specification_id, definition_version, horizon_days, aggregation_rule_id,
    normalization_rule_id, weight_policy_id, coverage_rule_id, parameters
) values (
    'portfolio-alpha-smoke', 'v1', 20, 'WEIGHTED_ABS_MEAN',
    'SMOKE_NORM', 'PORTFOLIO_SMOKE_WEIGHTS', 'ABS_WEIGHT_COVERAGE',
    '{"minimum_coverage":"1.0"}'::jsonb
);

insert into zk.alpha_factor_weights (
    specification_id, definition_version, admission_id, weight
) values
    ('portfolio-alpha-smoke', 'v1', 'alpha-smoke-adm-value', 1.0),
    ('portfolio-alpha-smoke', 'v1', 'alpha-smoke-adm-mom', 1.0);

begin;
insert into zk.alpha_runs (
    alpha_run_id, specification_id, definition_version, security_id, evaluated_at,
    alpha_field, status, alpha_value, coverage, planned_factor_count,
    available_factor_count, planned_absolute_weight, available_absolute_weight
) values
    ('portfolio-alpha-A', 'portfolio-alpha-smoke', 'v1', '74000000-0000-0000-0000-000000000002'::uuid, now(), 'Alpha20', 'SCORED', 0.90, 1.0, 2, 2, 2.0, 2.0),
    ('portfolio-alpha-B', 'portfolio-alpha-smoke', 'v1', '74000000-0000-0000-0000-000000000003'::uuid, now(), 'Alpha20', 'SCORED', 0.80, 1.0, 2, 2, 2.0, 2.0),
    ('portfolio-alpha-C', 'portfolio-alpha-smoke', 'v1', '74000000-0000-0000-0000-000000000004'::uuid, now(), 'Alpha20', 'SCORED', 0.70, 1.0, 2, 2, 2.0, 2.0),
    ('portfolio-alpha-D', 'portfolio-alpha-smoke', 'v1', '74000000-0000-0000-0000-000000000005'::uuid, now(), 'Alpha20', 'SCORED', -0.10, 1.0, 2, 2, 2.0, 2.0);

insert into zk.alpha_run_contributions (
    alpha_run_id, admission_id, raw_signal_value, normalization_rule_id,
    applicability_state, accounting_comparability_state,
    normalized_value, weight, weighted_contribution
) values
    ('portfolio-alpha-A', 'alpha-smoke-adm-value', 0.90, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', 0.90, 1.0, 0.90),
    ('portfolio-alpha-A', 'alpha-smoke-adm-mom', 0.90, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', 0.90, 1.0, 0.90),
    ('portfolio-alpha-B', 'alpha-smoke-adm-value', 0.80, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', 0.80, 1.0, 0.80),
    ('portfolio-alpha-B', 'alpha-smoke-adm-mom', 0.80, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', 0.80, 1.0, 0.80),
    ('portfolio-alpha-C', 'alpha-smoke-adm-value', 0.70, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', 0.70, 1.0, 0.70),
    ('portfolio-alpha-C', 'alpha-smoke-adm-mom', 0.70, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', 0.70, 1.0, 0.70),
    ('portfolio-alpha-D', 'alpha-smoke-adm-value', -0.10, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', -0.10, 1.0, -0.10),
    ('portfolio-alpha-D', 'alpha-smoke-adm-mom', -0.10, 'SMOKE_NORM', 'APPLIES', 'COMPARABLE', -0.10, 1.0, -0.10);
commit;

insert into zk.confidence_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    confidence_protocol_id, universe_rule_version,
    hypothesis, success_criteria, preregistered_at,
    minimum_weight_coverage, signal_eligibility_threshold
) values (
    'portfolio-confidence-smoke', 'v1', 20,
    'portfolio-alpha-smoke', 'v1',
    'portfolio-confidence-protocol', 'universe-v1',
    'Portfolio smoke confidence support.',
    'Only well-supported Alpha reaches the portfolio.',
    timestamptz '2026-09-01 00:00:00+00',
    1.0, 0.60
);

insert into zk.confidence_dimensions (
    specification_id, definition_version, dimension_id, kind, required,
    max_age_days, weight, bad_reference, good_reference, hard_floor
) values (
    'portfolio-confidence-smoke', 'v1', 'support', 'FACTOR_EVIDENCE',
    true, 5, 1.0, 0.0, 1.0, 0.50
);

insert into zk.confidence_observations (
    observation_id, security_id, dimension_id, confidence_protocol_id,
    raw_value, window_start, window_end, available_at, source_reference
) values
    ('portfolio-confidence-obs-A', '74000000-0000-0000-0000-000000000002'::uuid, 'support', 'portfolio-confidence-protocol', 0.90, timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'support-A'),
    ('portfolio-confidence-obs-B', '74000000-0000-0000-0000-000000000003'::uuid, 'support', 'portfolio-confidence-protocol', 0.80, timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'support-B'),
    ('portfolio-confidence-obs-C', '74000000-0000-0000-0000-000000000004'::uuid, 'support', 'portfolio-confidence-protocol', 0.70, timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'support-C'),
    ('portfolio-confidence-obs-D', '74000000-0000-0000-0000-000000000005'::uuid, 'support', 'portfolio-confidence-protocol', 0.90, timestamptz '2026-09-20 00:00:00+00', timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 'support-D');

begin;
insert into zk.confidence_runs (
    confidence_run_id, specification_id, definition_version, alpha_run_id,
    prediction_timestamp, source_alpha_value, decision, confidence_score,
    evidence_weight_coverage, available_weight, total_weight
) values
    ('portfolio-confidence-A', 'portfolio-confidence-smoke', 'v1', 'portfolio-alpha-A', timestamptz '2026-10-04 00:00:00+00', 0.90, 'SIGNAL_ELIGIBLE', 0.90, 1.0, 1.0, 1.0),
    ('portfolio-confidence-B', 'portfolio-confidence-smoke', 'v1', 'portfolio-alpha-B', timestamptz '2026-10-04 00:00:00+00', 0.80, 'SIGNAL_ELIGIBLE', 0.80, 1.0, 1.0, 1.0),
    ('portfolio-confidence-C', 'portfolio-confidence-smoke', 'v1', 'portfolio-alpha-C', timestamptz '2026-10-04 00:00:00+00', 0.70, 'SIGNAL_ELIGIBLE', 0.70, 1.0, 1.0, 1.0),
    ('portfolio-confidence-D', 'portfolio-confidence-smoke', 'v1', 'portfolio-alpha-D', timestamptz '2026-10-04 00:00:00+00', -0.10, 'SIGNAL_ELIGIBLE', 0.90, 1.0, 1.0, 1.0);

insert into zk.confidence_dimension_results (
    confidence_run_id, dimension_id, availability, observation_id,
    raw_value, normalized_quality, weight, weighted_contribution,
    hard_floor, hard_floor_pass, age_days
) values
    ('portfolio-confidence-A', 'support', 'AVAILABLE', 'portfolio-confidence-obs-A', 0.90, 0.90, 1.0, 0.90, 0.50, true, 1.0),
    ('portfolio-confidence-B', 'support', 'AVAILABLE', 'portfolio-confidence-obs-B', 0.80, 0.80, 1.0, 0.80, 0.50, true, 1.0),
    ('portfolio-confidence-C', 'support', 'AVAILABLE', 'portfolio-confidence-obs-C', 0.70, 0.70, 1.0, 0.70, 0.50, true, 1.0),
    ('portfolio-confidence-D', 'support', 'AVAILABLE', 'portfolio-confidence-obs-D', 0.90, 0.90, 1.0, 0.90, 0.50, true, 1.0);
commit;

insert into zk.portfolio_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    confidence_specification_id, confidence_definition_version,
    universe_rule_version, hypothesis, success_criteria, preregistered_at,
    selection_rule, sizing_rule, rebalance_rule_id,
    target_position_count, minimum_position_count, minimum_alpha_value,
    target_invested_weight, max_single_name_weight, max_sector_weight,
    max_participation_rate, execution_days, max_liquidity_age_days,
    maximum_one_way_turnover
) values (
    'portfolio-smoke', 'v1', 20,
    'portfolio-alpha-smoke', 'v1',
    'portfolio-confidence-smoke', 'v1',
    'universe-v1',
    'Eligible Alpha can be converted into a feasible long-only portfolio.',
    'Respect explicit sizing, caps, liquidity, turnover and costs.',
    timestamptz '2026-09-01 00:00:00+00',
    'TOP_ALPHA', 'EQUAL_WEIGHT', 'REBALANCE_TEST_ONLY',
    3, 2, 0.0,
    0.90, 0.40, 0.60,
    0.10, 2, 5, 1.0
);

begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-run-constructed', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'CONSTRUCTED',
    0.10, 0.45, 0.90, 2700
);

insert into zk.portfolio_run_candidates (
    portfolio_run_id, security_id, sector_id,
    alpha_run_id, confidence_run_id, alpha_value, confidence_score, eligible
) values
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 'portfolio-alpha-A', 'portfolio-confidence-A', 0.90, 0.90, true),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 'portfolio-alpha-B', 'portfolio-confidence-B', 0.80, 0.80, true),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 'portfolio-alpha-C', 'portfolio-confidence-C', 0.70, 0.70, true),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000005'::uuid, 'RETAIL', 'portfolio-alpha-D', 'portfolio-confidence-D', -0.10, 0.90, false);

insert into zk.portfolio_execution_evidence (
    portfolio_run_id, security_id, window_end, available_at,
    average_daily_notional, commission_bps, half_spread_bps,
    slippage_bps, market_impact_bps, source_reference
) values
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000002'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-A'),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000003'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-B'),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000004'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-C');

insert into zk.portfolio_target_positions (
    portfolio_run_id, security_id, sector_id,
    alpha_value, confidence_score, rank, target_weight
) values
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 0.90, 0.90, 1, 0.30),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 0.80, 0.80, 2, 0.30),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 0.70, 0.70, 3, 0.30);

insert into zk.portfolio_orders (
    portfolio_run_id, security_id, side,
    current_weight, target_weight, delta_weight,
    trade_notional, max_trade_notional,
    commission_cost, spread_cost, slippage_cost, market_impact_cost, total_cost
) values
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000002'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000003'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900),
    ('portfolio-run-constructed', '74000000-0000-0000-0000-000000000004'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900);
commit;

begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-run-exit-smoke', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'CONSTRUCTED',
    0.10, 0.60, 1.20, 3600
);

insert into zk.portfolio_run_candidates (
    portfolio_run_id, security_id, sector_id,
    alpha_run_id, confidence_run_id, alpha_value, confidence_score, eligible
) values
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 'portfolio-alpha-A', 'portfolio-confidence-A', 0.90, 0.90, true),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 'portfolio-alpha-B', 'portfolio-confidence-B', 0.80, 0.80, true),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 'portfolio-alpha-C', 'portfolio-confidence-C', 0.70, 0.70, true),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000005'::uuid, 'RETAIL', 'portfolio-alpha-D', 'portfolio-confidence-D', -0.10, 0.90, false);

insert into zk.portfolio_current_holdings (
    portfolio_run_id, security_id, weight
) values (
    'portfolio-run-exit-smoke',
    '74000000-0000-0000-0000-000000000005'::uuid,
    0.30
);

insert into zk.portfolio_execution_evidence (
    portfolio_run_id, security_id, window_end, available_at,
    average_daily_notional, commission_bps, half_spread_bps,
    slippage_bps, market_impact_bps, source_reference
) values
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000002'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-A-exit'),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000003'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-B-exit'),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000004'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-C-exit'),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000005'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-D-exit');

insert into zk.portfolio_target_positions (
    portfolio_run_id, security_id, sector_id,
    alpha_value, confidence_score, rank, target_weight
) values
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 0.90, 0.90, 1, 0.30),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 0.80, 0.80, 2, 0.30),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 0.70, 0.70, 3, 0.30);

insert into zk.portfolio_orders (
    portfolio_run_id, security_id, side,
    current_weight, target_weight, delta_weight,
    trade_notional, max_trade_notional,
    commission_cost, spread_cost, slippage_cost, market_impact_cost, total_cost
) values
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000002'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000003'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000004'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900),
    ('portfolio-run-exit-smoke', '74000000-0000-0000-0000-000000000005'::uuid, 'SELL', 0.30, 0.0, -0.30, 300000, 2000000, 150, 300, 150, 300, 900);
commit;

begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-run-liquidity-infeasible', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'INFEASIBLE_LIQUIDITY',
    0.10, 0.45, 0.90, 1800
);

insert into zk.portfolio_run_candidates (
    portfolio_run_id, security_id, sector_id,
    alpha_run_id, confidence_run_id, alpha_value, confidence_score, eligible
) values
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 'portfolio-alpha-A', 'portfolio-confidence-A', 0.90, 0.90, true),
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 'portfolio-alpha-B', 'portfolio-confidence-B', 0.80, 0.80, true),
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 'portfolio-alpha-C', 'portfolio-confidence-C', 0.70, 0.70, true),
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000005'::uuid, 'RETAIL', 'portfolio-alpha-D', 'portfolio-confidence-D', -0.10, 0.90, false);

insert into zk.portfolio_execution_evidence (
    portfolio_run_id, security_id, window_end, available_at,
    average_daily_notional, commission_bps, half_spread_bps,
    slippage_bps, market_impact_bps, source_reference
) values
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000002'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-A-partial'),
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000003'::uuid, timestamptz '2026-10-03 00:00:00+00', timestamptz '2026-10-03 01:00:00+00', 10000000, 5, 10, 5, 10, 'liq-B-partial');

insert into zk.portfolio_target_positions (
    portfolio_run_id, security_id, sector_id,
    alpha_value, confidence_score, rank, target_weight
) values
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 0.90, 0.90, 1, 0.30),
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 0.80, 0.80, 2, 0.30),
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 0.70, 0.70, 3, 0.30);

insert into zk.portfolio_orders (
    portfolio_run_id, security_id, side,
    current_weight, target_weight, delta_weight,
    trade_notional, max_trade_notional,
    commission_cost, spread_cost, slippage_cost, market_impact_cost, total_cost
) values
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000002'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900),
    ('portfolio-run-liquidity-infeasible', '74000000-0000-0000-0000-000000000003'::uuid, 'BUY', 0.0, 0.30, 0.30, 300000, 2000000, 150, 300, 150, 300, 900);

insert into zk.portfolio_infeasibility_reasons (
    portfolio_run_id, reason_code, security_id
) values (
    'portfolio-run-liquidity-infeasible',
    'MISSING_EXECUTION_EVIDENCE',
    '74000000-0000-0000-0000-000000000004'::uuid
);
commit;

select portfolio_run_id, status, cash_weight, one_way_turnover, total_estimated_cost
from zk.portfolio_runs
where specification_id = 'portfolio-smoke';
