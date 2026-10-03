\set ON_ERROR_STOP on
insert into zk.dynamic_weighting_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    minimum_metric_coverage, max_evidence_age_days,
    multiplier_floor, multiplier_ceiling, gross_exposure_policy, stage
) values (
    'dynamic-production-attempt', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    0.75, 120, 0.5, 1.5, 'NONE', 'PRODUCTION'
);
