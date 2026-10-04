\set ON_ERROR_STOP on
begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-bad-candidate-run', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'INFEASIBLE_INSUFFICIENT_ELIGIBLE',
    1.0, 0.0, 0.0, 0.0
);

insert into zk.portfolio_run_candidates (
    portfolio_run_id, security_id, sector_id,
    alpha_run_id, confidence_run_id, alpha_value, confidence_score, eligible
) values (
    'portfolio-bad-candidate-run',
    '74000000-0000-0000-0000-000000000002'::uuid,
    'BANK', 'portfolio-alpha-A', 'portfolio-confidence-A',
    0.91, 0.90, true
);
