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
