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
    'https://example.invalid/test-record-1-again',
    'application/json',
    '{"kind":"duplicate"}'::jsonb,
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    timestamptz '2025-03-01 18:00:00+03',
    timestamptz '2025-03-01 18:07:00+03'
);
