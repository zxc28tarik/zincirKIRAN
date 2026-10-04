\set ON_ERROR_STOP on
insert into zk.portfolio_infeasibility_reasons (
    portfolio_run_id, reason_code, security_id
) values (
    'portfolio-run-constructed',
    'MAXIMUM_ONE_WAY_TURNOVER_EXCEEDED',
    null
);
