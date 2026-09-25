\set ON_ERROR_STOP on

-- Schema existence and required tables.
do $$
declare
    missing_count integer;
begin
    select count(*) into missing_count
    from (
        values
            ('source_registry'),
            ('companies'),
            ('securities'),
            ('security_identifiers'),
            ('prices'),
            ('financial_facts'),
            ('financial_revisions'),
            ('corporate_actions'),
            ('shares_history'),
            ('universe_history')
    ) as required(table_name)
    where not exists (
        select 1
        from information_schema.tables t
        where t.table_schema = 'zk'
          and t.table_name = required.table_name
    );

    if missing_count <> 0 then
        raise exception 'PIT schema is missing % required tables', missing_count;
    end if;
end
$$;

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

-- The same logical fact/revision must not be silently inserted twice.
do $$
begin
    begin
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
            9999.00,
            'TRY',
            timestamptz '2025-03-01 18:00:00+03',
            timestamptz '2025-03-01 18:00:00+03',
            'r1',
            '00000000-0000-0000-0000-000000000001'
        );
        raise exception 'Expected duplicate financial-fact rejection';
    exception
        when unique_violation then
            null;
    end;
end
$$;

-- Invalid free-float ratios must be rejected.
do $$
begin
    begin
        insert into zk.shares_history (
            company_id,
            effective_from,
            shares_outstanding,
            free_float_ratio,
            source_id,
            available_at
        )
        values (
            '10000000-0000-0000-0000-000000000001',
            date '2025-01-01',
            1000000,
            1.50,
            '00000000-0000-0000-0000-000000000001',
            timestamptz '2025-01-01 00:00:00+03'
        );
        raise exception 'Expected free_float_ratio check rejection';
    exception
        when check_violation then
            null;
    end;
end
$$;

-- Public should not have schema privileges.
do $$
begin
    if has_schema_privilege('public', 'zk', 'USAGE') then
        raise exception 'PUBLIC unexpectedly has USAGE on zk schema';
    end if;
end
$$;
