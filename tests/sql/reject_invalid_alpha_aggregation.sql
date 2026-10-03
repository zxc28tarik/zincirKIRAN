\set ON_ERROR_STOP on

insert into zk.alpha_aggregation_specs (
    specification_id, definition_version, horizon_days,
    aggregation_rule_id, normalization_rule_id, weight_policy_id, coverage_rule_id
) values (
    'alpha-bad', 'v1', 21,
    'RULE_A', 'NORM_A', 'WEIGHT_A', ''
);
