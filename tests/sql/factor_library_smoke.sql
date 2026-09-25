\set ON_ERROR_STOP on

insert into zk.factor_registry (
    factor_id, definition_version, economic_family, economic_concept_key,
    specification, expected_direction, required_fields
) values (
    'smoke_book_to_price', 'v1', 'VALUE', 'book_value_yield',
    'book_equity / market_cap', 'HIGHER_IS_BETTER',
    '["book_equity", "market_cap"]'::jsonb
);

select factor_id, stage, evidence_status
from zk.factor_registry
where factor_id = 'smoke_book_to_price';
