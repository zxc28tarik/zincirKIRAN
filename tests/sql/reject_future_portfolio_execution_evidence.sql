\set ON_ERROR_STOP on
begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-future-evidence-run', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'INFEASIBLE_INSUFFICIENT_ELIGIBLE',
    1.0, 0.0, 0.0, 0.0
);

insert into zk.portfolio_execution_evidence (
    portfolio_run_id, security_id, window_end, available_at,
    average_daily_notional, commission_bps, half_spread_bps,
    slippage_bps, market_impact_bps, source_reference
) values (
    'portfolio-future-evidence-run',
    '74000000-0000-0000-0000-000000000002'::uuid,
    timestamptz '2026-10-05 00:00:00+00',
    timestamptz '2026-10-05 01:00:00+00',
    10000000, 5, 10, 5, 10, 'future'
);
