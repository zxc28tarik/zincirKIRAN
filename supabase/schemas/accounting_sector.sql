-- Zincir Kıran — Accounting & Sector Engine schema v0.1

alter table zk.financial_facts
    add constraint financial_facts_restatement_status_chk
    check (
        restatement_status is null
        or restatement_status in ('ORIGINAL', 'RESTATED', 'UNKNOWN')
    );

create table zk.feature_applicability (
    feature_id text not null,
    company_type text not null,
    decision_version text not null,
    applicability_state text not null,
    rationale text,
    evidence_ref text,
    created_at timestamptz not null default now(),
    primary key (feature_id, company_type, decision_version),
    constraint feature_applicability_feature_id_chk
        check (length(trim(feature_id)) > 0),
    constraint feature_applicability_company_type_chk
        check (length(trim(company_type)) > 0),
    constraint feature_applicability_version_chk
        check (length(trim(decision_version)) > 0),
    constraint feature_applicability_state_chk
        check (applicability_state in ('APPLIES', 'DOES_NOT_APPLY', 'UNDECIDED'))
);

create index feature_applicability_lookup_idx
    on zk.feature_applicability(feature_id, company_type, created_at desc);
