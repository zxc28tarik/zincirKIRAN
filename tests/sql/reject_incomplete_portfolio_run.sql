\set ON_ERROR_STOP on
begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-incomplete-run', 'portfolio-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'CONSTRUCTED',
    1.0, 0.0, 0.0, 0.0
);
commit;
