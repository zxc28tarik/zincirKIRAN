\set ON_ERROR_STOP on

insert into zk.alpha_aggregation_specs (
    specification_id, definition_version, horizon_days,
    aggregation_rule_id, normalization_rule_id, weight_policy_id,
    coverage_rule_id, parameters
) values (
    'alpha-smoke', 'v1', 20,
    'TEST_RULE', 'TEST_NORMALIZATION', 'TEST_WEIGHT_POLICY',
    'TEST_COVERAGE_RULE', '{"note":"smoke-only"}'::jsonb
);

select specification_id, definition_version, horizon_days
from zk.alpha_aggregation_specs
where specification_id = 'alpha-smoke';
