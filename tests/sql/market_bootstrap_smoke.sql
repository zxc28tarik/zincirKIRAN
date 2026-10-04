\set ON_ERROR_STOP on

insert into zk.market_bootstrap_artifacts (
 artifact_id,source_repository,source_commit,source_path,sha256,authority,
 row_count,coverage_start,coverage_end,scope_note
) values
(
 'v24-daily-member-prices',
 'zxc28tarik/TOTAL-RASYO-HESAPLAYICI',
 '883e680a2564e38f4c08a21bc88aa95b8f164036',
 'data/backtest_sources/yahoo_resolved/historical_member_prices_resolved_2020-07_2026-08.csv.gz',
 'b3413840f7516b2dd51611efa9139b28ddee1eb2d11d14dd418097138dd33141',
 'VALIDATED_DERIVED_MARKET_DATA',271267,'2020-07','2026-08','Validated Yahoo-derived market panel.'
),
(
 'v24-monthly-execution-panel',
 'zxc28tarik/TOTAL-RASYO-HESAPLAYICI',
 '883e680a2564e38f4c08a21bc88aa95b8f164036',
 'data/backtest_sources/yahoo_resolved/monthly_member_signal_price_coverage.csv',
 'a3b14014aa4d3ff16a082bc0dac64346b906f4b7720aeae5a8c449a2add314f2',
 'VALIDATED_EXECUTION_PANEL',6000,'2021-08','2026-07','Exact BIST100 monthly execution panel.'
);

select artifact_id,authority,row_count
from zk.market_bootstrap_artifacts
order by artifact_id;
