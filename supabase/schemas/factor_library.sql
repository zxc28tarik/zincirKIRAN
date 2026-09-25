-- Zincir Kıran — Candidate Factor Library schema v0.1

create table zk.factor_registry (
    factor_id text not null,
    definition_version text not null,
    economic_family text not null,
    economic_concept_key text not null,
    specification text not null,
    expected_direction text not null default 'UNDECIDED',
    required_fields jsonb not null,
    stage text not null default 'CANDIDATE',
    evidence_status text not null default 'UNREVIEWED',
    evidence_refs jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    primary key (factor_id, definition_version),
    constraint factor_registry_family_chk check (economic_family in (
        'VALUE', 'PROFITABILITY', 'QUALITY', 'INVESTMENT_DISCIPLINE',
        'FUNDAMENTAL_ACCELERATION', 'PRICE_MOMENTUM', 'EARNINGS_MOMENTUM',
        'RISK', 'LIQUIDITY', 'SIZE_CONTROL'
    )),
    constraint factor_registry_direction_chk check (expected_direction in (
        'HIGHER_IS_BETTER', 'LOWER_IS_BETTER', 'CONTEXTUAL', 'UNDECIDED'
    )),
    constraint factor_registry_candidate_only_chk check (stage = 'CANDIDATE'),
    constraint factor_registry_evidence_status_chk check (evidence_status in ('UNREVIEWED', 'SOURCED')),
    constraint factor_registry_required_fields_chk check (
        jsonb_typeof(required_fields) = 'array' and jsonb_array_length(required_fields) > 0
    ),
    constraint factor_registry_evidence_refs_chk check (jsonb_typeof(evidence_refs) = 'array'),
    constraint factor_registry_unreviewed_refs_chk check (
        evidence_status <> 'UNREVIEWED' or jsonb_array_length(evidence_refs) = 0
    ),
    constraint factor_registry_text_chk check (
        length(trim(factor_id)) > 0
        and length(trim(definition_version)) > 0
        and length(trim(economic_concept_key)) > 0
        and length(trim(specification)) > 0
    )
);

create index factor_registry_family_idx
    on zk.factor_registry(economic_family, economic_concept_key, factor_id);

create function zk.reject_factor_registry_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'factor definitions are append-only; create a new definition_version';
end;
$$;

create trigger factor_registry_immutable_trg
before update or delete on zk.factor_registry
for each row execute function zk.reject_factor_registry_mutation();
