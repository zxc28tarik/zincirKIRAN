\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, expected_direction, required_fields
) values (
    'lab_smoke_factor', 'v1', 'VALUE', 'lab_smoke',
    'smoke specification', 'HIGHER_IS_BETTER', '["x"]'::jsonb
);

insert into zk.factor_experiments (
    experiment_id, factor_id, factor_definition_version, horizon_days,
    data_snapshot_id, universe_rule_version, quantile_count, cost_model_id,
    hypothesis, expected_direction, preregistered_at
) values (
    'lab-smoke-exp', 'lab_smoke_factor', 'v1', 20,
    'snapshot-v1', 'universe-v1', 5, 'cost-v1',
    'Higher signal predicts higher excess return.',
    'HIGHER_IS_BETTER', timestamptz '2026-09-25 12:00:00+03'
);

insert into zk.factor_lab_results (
    experiment_id, total_periods, valid_ic_periods, mean_ic, icir,
    mean_coverage, monotonicity, top_vs_market, bottom_vs_market,
    top_minus_bottom, average_turnover, gross_spread, cost_adjusted_spread
) values (
    'lab-smoke-exp', 10, 9, 0.05, 0.40,
    0.90, 0.80, 0.03, -0.02, 0.05, 0.20, 0.05, 0.048
);

insert into zk.factor_lab_liquidity_results (
    experiment_id, liquidity_tier, sample_size, coverage, ic,
    monotonicity, top_vs_market, bottom_vs_market, top_minus_bottom
) values (
    'lab-smoke-exp', 'LIQUID_25', 50, 0.85, 0.04,
    0.75, 0.025, -0.015, 0.04
);

select experiment_id, mean_ic, top_vs_market, top_minus_bottom
from zk.factor_lab_results
where experiment_id = 'lab-smoke-exp';
