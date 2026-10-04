-- Zincir Kıran — Historical KAP Version Enumeration schema v0.1

create table zk.kap_enumeration_runs (
    run_id text primary key,
    captured_at timestamptz not null,
    windows_requested integer not null,
    windows_succeeded integer not null,
    windows_failed integer not null,
    distinct_disclosures integer not null,
    correction_edges integer not null,
    status text not null,
    completeness_guaranteed boolean not null default false,
    blocker_code text not null,
    created_at timestamptz not null default now(),
    constraint kap_enum_counts_chk check (
        windows_requested >= 0
        and windows_succeeded >= 0
        and windows_failed >= 0
        and windows_succeeded + windows_failed = windows_requested
        and distinct_disclosures >= 0
        and correction_edges >= 0
    ),
    constraint kap_enum_status_chk check (
        status in (
            'ENUMERATION_NOT_RUN',
            'ENUMERATED_PARTIAL',
            'ENUMERATED_WITH_CORRECTION_CHAINS'
        )
    ),
    constraint kap_enum_completeness_chk check (completeness_guaranteed = false),
    constraint kap_enum_blocker_chk check (length(trim(blocker_code)) > 0)
);

create function zk.reject_kap_enum_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'KAP enumeration records are append-only';
end;
$fn$;

create trigger kap_enumeration_runs_immutable_trg
before update or delete on zk.kap_enumeration_runs
for each row execute function zk.reject_kap_enum_mutation();

create table zk.kap_enumeration_windows (
    run_id text not null references zk.kap_enumeration_runs(run_id),
    window_id text not null,
    start_at timestamptz not null,
    end_at timestamptz not null,
    http_status integer,
    request_sha256 text,
    response_sha256 text,
    result_count integer,
    status text not null,
    created_at timestamptz not null default now(),
    primary key (run_id, window_id),
    constraint kap_enum_window_time_chk check (start_at < end_at),
    constraint kap_enum_window_status_chk check (
        status in ('SUCCESS','FAILED','NOT_RUN')
    ),
    constraint kap_enum_window_hash_chk check (
        (request_sha256 is null or request_sha256 ~ '^[0-9a-f]{64}$')
        and (response_sha256 is null or response_sha256 ~ '^[0-9a-f]{64}$')
    ),
    constraint kap_enum_window_result_chk check (result_count is null or result_count >= 0)
);

create trigger kap_enumeration_windows_immutable_trg
before update or delete on zk.kap_enumeration_windows
for each row execute function zk.reject_kap_enum_mutation();

create table zk.kap_disclosure_versions (
    run_id text not null references zk.kap_enumeration_runs(run_id),
    disclosure_id text not null,
    published_at timestamptz not null,
    report_year integer,
    report_period integer,
    stock_codes text[] not null,
    modify_status text,
    response_sha256 text not null,
    created_at timestamptz not null default now(),
    primary key (run_id, disclosure_id),
    constraint kap_disclosure_version_hash_chk check (
        response_sha256 ~ '^[0-9a-f]{64}$'
    ),
    constraint kap_disclosure_stock_codes_chk check (
        cardinality(stock_codes) >= 1
    )
);

create trigger kap_disclosure_versions_immutable_trg
before update or delete on zk.kap_disclosure_versions
for each row execute function zk.reject_kap_enum_mutation();

create table zk.kap_correction_edges (
    run_id text not null references zk.kap_enumeration_runs(run_id),
    older_disclosure_id text not null,
    newer_disclosure_id text not null,
    older_published_at timestamptz not null,
    newer_published_at timestamptz not null,
    relation_label text not null,
    created_at timestamptz not null default now(),
    primary key (run_id, older_disclosure_id, newer_disclosure_id),
    constraint kap_correction_time_chk check (older_published_at < newer_published_at),
    constraint kap_correction_label_chk check (length(trim(relation_label)) > 0)
);

create trigger kap_correction_edges_immutable_trg
before update or delete on zk.kap_correction_edges
for each row execute function zk.reject_kap_enum_mutation();
