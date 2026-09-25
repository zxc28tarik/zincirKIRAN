\set ON_ERROR_STOP on

insert into zk.source_registry (source_id, name, source_type)
values ('00000000-0000-0000-0000-000000000901', 'TEST_ACCOUNTING', 'TEST');

insert into zk.companies (company_id, legal_name)
values ('00000000-0000-0000-0000-000000000902', 'TEST ACCOUNTING CO');

insert into zk.financial_facts (
    company_id, statement_type, metric_id, period_end, value,
    available_at, revision_id, source_id, restatement_status
) values (
    '00000000-0000-0000-0000-000000000902',
    'INCOME_STATEMENT',
    'revenue',
    date '2025-12-31',
    100,
    timestamptz '2026-03-01 12:00:00+03',
    'r1',
    '00000000-0000-0000-0000-000000000901',
    'MAGIC_FIXED'
);
