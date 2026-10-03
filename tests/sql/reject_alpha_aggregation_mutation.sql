\set ON_ERROR_STOP on

insert into zk.alpha_aggregation_specs (
    specification_id, definition_version, horizon_days,
    aggregation_rule_id, normalization_rule_id, weight_policy_id, coverage_rule_id
) values (
    'alpha-immutable', 'v1', 60,
    'RULE_A', 'NORM_A', 'WEIGHT_A', 'COVERAGE_A'
);

update zk.alpha_aggregation_specs
set weight_policy_id = 'CHANGED_AFTER_RESULTS'
where specification_id = 'alpha-immutable'
  and definition_version = 'v1';
