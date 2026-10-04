\set ON_ERROR_STOP on
begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-missing-liquidity-run', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'CONSTRUCTED',
    0.10, 0.45, 0.90, 0
);

insert into zk.portfolio_run_candidates (
    portfolio_run_id, security_id, sector_id,
    alpha_run_id, confidence_run_id, alpha_value, confidence_score, eligible
) values
    ('portfolio-missing-liquidity-run', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 'portfolio-alpha-A', 'portfolio-confidence-A', 0.90, 0.90, true),
    ('portfolio-missing-liquidity-run', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 'portfolio-alpha-B', 'portfolio-confidence-B', 0.80, 0.80, true),
    ('portfolio-missing-liquidity-run', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 'portfolio-alpha-C', 'portfolio-confidence-C', 0.70, 0.70, true),
    ('portfolio-missing-liquidity-run', '74000000-0000-0000-0000-000000000005'::uuid, 'RETAIL', 'portfolio-alpha-D', 'portfolio-confidence-D', -0.10, 0.90, false);

insert into zk.portfolio_target_positions (
    portfolio_run_id, security_id, sector_id,
    alpha_value, confidence_score, rank, target_weight
) values
    ('portfolio-missing-liquidity-run', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 0.90, 0.90, 1, 0.30),
    ('portfolio-missing-liquidity-run', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 0.80, 0.80, 2, 0.30),
    ('portfolio-missing-liquidity-run', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 0.70, 0.70, 3, 0.30);
commit;
