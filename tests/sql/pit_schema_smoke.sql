\set ON_ERROR_STOP on

-- Required schema and tables.
select (
    to_regnamespace('zk') is not null
    and (
        select count(*) = 10
        from information_schema.tables
        where table_schema = 'zk'
          and table_name in (
              'source_registry',
              'companies',
              'securities',
              'security_identifiers',
              'prices',
              'financial_facts',
              'financial_revisions',
              'corporate_actions',
              'shares_history',
              'universe_history'
          )
    )
) as schema_ok \gset

\if :schema_ok
\else
\echo 'PIT schema/table verification failed'
\quit 1
\endif

-- PUBLIC must not be able to use the internal schema.
select (not has_schema_privilege('public', 'zk', 'USAGE')) as public_locked \gset

\if :public_locked
\else
\echo 'PUBLIC unexpectedly has USAGE on zk schema'
\quit 1
\endif

-- Structural guards must exist.
select exists (
    select 1
    from pg_indexes
    where schemaname = 'zk'
      and indexname = 'financial_facts_identity_uidx'
) as financial_identity_guard_ok \gset

\if :financial_identity_guard_ok
\else
\echo 'financial_facts identity guard is missing'
\quit 1
\endif

select exists (
    select 1
    from pg_constraint
    where conname = 'shares_history_free_float_ratio_chk'
      and conrelid = 'zk.shares_history'::regclass
) as free_float_guard_ok \gset

\if :free_float_guard_ok
\else
\echo 'free-float ratio check constraint is missing'
\quit 1
\endif

-- Minimal provenance chain and PIT rows.
insert into zk.source_registry (source_id, name, source_type, timestamp_quality)
values ('00000000-0000-0000-0000-000000000001', 'TEST_SOURCE', 'TEST', 'EXACT');

insert into zk.companies (company_id, legal_name, primary_source_id)
values (
    '10000000-0000-0000-0000-000000000001',
    'Test Company A.S.',
    '00000000-0000-0000-0000-000000000001'
);

insert into zk.securities (security_id, company_id)
values (
    '20000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001'
);

insert into zk.security_identifiers (
    security_id, ticker, isin, valid_from, source_id
)
values (
    '20000000-0000-0000-0000-000000000001',
    'TEST',
    'TRTEST000001',
    date '2025-01-01',
    '00000000-0000-0000-0000-000000000001'
);

insert into zk.prices (
    security_id,
    trade_date,
    close,
    source_id,
    available_at
)
values (
    '20000000-0000-0000-0000-000000000001',
    date '2025-01-02',
    100.00,
    '00000000-0000-0000-0000-000000000001',
    timestamptz '2025-01-02 18:30:00+03'
);

insert into zk.financial_facts (
    company_id,
    statement_type,
    metric_id,
    period_end,
    value,
    currency,
    reported_at,
    available_at,
    revision_id,
    source_id
)
values (
    '10000000-0000-0000-0000-000000000001',
    'INCOME',
    'revenue',
    date '2024-12-31',
    1000.00,
    'TRY',
    timestamptz '2025-03-01 18:00:00+03',
    timestamptz '2025-03-01 18:00:00+03',
    'r1',
    '00000000-0000-0000-0000-000000000001'
);

select (
    (select count(*) from zk.source_registry) = 1
    and (select count(*) from zk.companies) = 1
    and (select count(*) from zk.securities) = 1
    and (select count(*) from zk.security_identifiers) = 1
    and (select count(*) from zk.prices) = 1
    and (select count(*) from zk.financial_facts) = 1
) as provenance_chain_ok \gset

\if :provenance_chain_ok
\else
\echo 'Minimal provenance/PIT insert chain failed'
\quit 1
\endif
