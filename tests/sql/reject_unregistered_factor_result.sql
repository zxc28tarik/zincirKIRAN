\set ON_ERROR_STOP on

insert into zk.factor_lab_results (
    experiment_id, total_periods, valid_ic_periods, mean_coverage
) values (
    'not-preregistered', 10, 10, 1.0
);
