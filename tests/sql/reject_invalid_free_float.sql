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
