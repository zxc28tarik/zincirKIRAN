\set ON_ERROR_STOP on
begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-bad-cost-run', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'CONSTRUCTED',
    0.70, 0.15, 0.30, 901
);

insert into zk.portfolio_run_candidates (
    portfolio_run_id, security_id, sector_id,
    alpha_run_id, confidence_run_id, alpha_value, confidence_score, eligible
) values (
    'portfolio-bad-cost-run',
    '74000000-0000-0000-0000-000000000002'::uuid,
    'BANK', 'portfolio-alpha-A', 'portfolio-confidence-A',
    0.90, 0.90, true
);

insert into zk.portfolio_target_positions (
    portfolio_run_id, security_id, sector_id,
    alpha_value, confidence_score, rank, target_weight
) values (
    'portfolio-bad-cost-run',
    '74000000-0000-0000-0000-000000000002'::uuid,
    'BANK', 0.90, 0.90, 1, 0.30
);

insert into zk.portfolio_execution_evidence (
    portfolio_run_id, security_id, window_end, available_at,
    average_daily_notional, commission_bps, half_spread_bps,
    slippage_bps, market_impact_bps, source_reference
) values (
    'portfolio-bad-cost-run',
    '74000000-0000-0000-0000-000000000002'::uuid,
    timestamptz '2026-10-03 00:00:00+00',
    timestamptz '2026-10-03 01:00:00+00',
    10000000, 5, 10, 5, 10, 'fresh'
);

insert into zk.portfolio_orders (
    portfolio_run_id, security_id, side,
    current_weight, target_weight, delta_weight,
    trade_notional, max_trade_notional,
    commission_cost, spread_cost, slippage_cost, market_impact_cost, total_cost
) values (
    'portfolio-bad-cost-run',
    '74000000-0000-0000-0000-000000000002'::uuid,
    'BUY', 0.0, 0.30, 0.30,
    300000, 2000000, 151, 300, 150, 300, 901
);
