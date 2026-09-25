\set ON_ERROR_STOP on

-- Required schema and tables.
select (
    to_regnamespace('zk') is not null
    and (
        select count(*) = 12
        from information_schema.tables
        where table_schema = 'zk'
          and table_name in (
              'source_registry',
              'ingestion_batches',
              'raw_records',
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
    from pg_indexes
    where schemaname = 'zk'
      and indexname = 'raw_records_identity_uidx'
) as raw_identity_guard_ok \gset

\if :raw_identity_guard_ok
\else
\echo 'raw_records identity guard is missing'
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

-- Minimal immutable-style RAW -> PIT provenance chain.
insert into zk.source_registry (source_id, name, source_type, timestamp_quality)
values ('00000000-0000-0000-0000-000000000001', 'TEST_SOURCE', 'TEST', 'EXACT');

insert into zk.ingestion_batches (
    batch_id,
    source_id,
    extractor_version,
    started_at,
    completed_at,
    status
)
values (
    '01000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    'test-extractor-v1',
    timestamptz '2025-03-01 18:05:00+03',
    timestamptz '2025-03-01 18:06:00+03',
    'COMPLETED'
);

insert into zk.raw_records (
    source_id,
    batch_id,
    source_record_key,
    source_url,
    content_type,
    payload,
    content_sha256,
    source_published_at,
    retrieved_at
)
values (
    '00000000-0000-0000-0000-000000000001',
    '01000000-0000-0000-0000-000000000001',
    'TEST_RECORD_1',
    'https://example.invalid/test-record-1',
    'application/json',
    '{"kind":"financial_report","period":"2024-12-31"}'::jsonb,
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    timestamptz '2025-03-01 18:00:00+03',
    timestamptz '2025-03-01 18:05:00+03'
);

select raw_record_id
from zk.raw_records
where source_id = '00000000-0000-0000-0000-000000000001'
  and source_record_key = 'TEST_RECORD_1'
\gset

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
    security_id,
    ticker,
    isin,
    valid_from,
    source_id,
    raw_record_id
)
values (
    '20000000-0000-0000-0000-000000000001',
    'TEST',
    'TRTEST000001',
    date '2025-01-01',
    '00000000-0000-0000-0000-000000000001',
    :raw_record_id
);

insert into zk.prices (
    security_id,
    trade_date,
    close,
    source_id,
    raw_record_id,
    available_at
)
values (
    '20000000-0000-0000-0000-000000000001',
    date '2025-01-02',
    100.00,
    '00000000-0000-0000-0000-000000000001',
    :raw_record_id,
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
    source_id,
    raw_record_id
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
    '00000000-0000-0000-0000-000000000001',
    :raw_record_id
);

select exists (
    select 1
    from zk.financial_facts ff
    join zk.raw_records rr
      on rr.raw_record_id = ff.raw_record_id
     and rr.source_id = ff.source_id
    join zk.ingestion_batches ib
      on ib.batch_id = rr.batch_id
     and ib.source_id = rr.source_id
    join zk.source_registry sr
      on sr.source_id = rr.source_id
    where ff.metric_id = 'revenue'
      and rr.source_record_key = 'TEST_RECORD_1'
      and ib.extractor_version = 'test-extractor-v1'
      and sr.name = 'TEST_SOURCE'
) as provenance_chain_ok \gset

\if :provenance_chain_ok
\else
\echo 'RAW -> PIT provenance chain failed'
\quit 1
\endif
