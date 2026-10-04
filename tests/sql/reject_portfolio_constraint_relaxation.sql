\set ON_ERROR_STOP on
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
    'portfolio-constraint-guard', 'v1', 20,
    'portfolio-alpha-smoke', 'v1',
    'portfolio-confidence-smoke', 'v1',
    'universe-v1', 'sector cap guard', 'must report infeasible',
    timestamptz '2026-09-01 00:00:00+00',
    'TOP_ALPHA', 'EQUAL_WEIGHT', 'TEST',
    3, 2, 0.0, 0.90, 0.60, 0.40, 0.10, 2, 5, 1.0
);

begin;
insert into zk.portfolio_runs (
    portfolio_run_id, specification_id, definition_version,
    prediction_timestamp, portfolio_notional, status,
    cash_weight, one_way_turnover, gross_turnover, total_estimated_cost
) values (
    'portfolio-constraint-relax-run', 'portfolio-constraint-guard', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    1000000, 'CONSTRUCTED',
    1.0, 0.0, 0.0, 0
);

insert into zk.portfolio_run_candidates (
    portfolio_run_id, security_id, sector_id,
    alpha_run_id, confidence_run_id, alpha_value, confidence_score, eligible
) values
    ('portfolio-constraint-relax-run', '74000000-0000-0000-0000-000000000002'::uuid, 'BANK', 'portfolio-alpha-A', 'portfolio-confidence-A', 0.90, 0.90, true),
    ('portfolio-constraint-relax-run', '74000000-0000-0000-0000-000000000003'::uuid, 'BANK', 'portfolio-alpha-B', 'portfolio-confidence-B', 0.80, 0.80, true),
    ('portfolio-constraint-relax-run', '74000000-0000-0000-0000-000000000004'::uuid, 'INDUSTRY', 'portfolio-alpha-C', 'portfolio-confidence-C', 0.70, 0.70, true);
commit;
