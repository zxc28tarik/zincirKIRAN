-- Zincir Kıran — Corporate Action Event Bootstrap schema v0.1

create table zk.corporate_action_evidence (
    event_id text not null,
    published_at timestamptz not null,
    ticker text not null,
    subject text not null,
    event_type text not null,
    authority text not null,
    source_sha256 text not null,
    source_system text not null,
    created_at timestamptz not null default now(),
    primary key (event_id, ticker),
    constraint corporate_action_event_type_chk check (
        event_type in (
            'CAPITAL_INCREASE','CAPITAL_DECREASE','MERGER','DEMERGER',
            'SHARE_CLASS_CHANGE','TICKER_CHANGE','AMBIGUOUS_SHARE_COUNT_ACTION'
        )
    ),
    constraint corporate_action_authority_chk check (
        authority in (
            'POSITIVE_EVENT_EVIDENCE',
            'COVERED_WINDOW_ABSENCE_EVIDENCE',
            'OFFICIAL_BORSA_LINEAGE'
        )
    ),
    constraint corporate_action_hash_chk check (source_sha256 ~ '^[0-9a-f]{64}$'),
    constraint corporate_action_text_chk check (
        length(trim(event_id)) > 0 and length(trim(ticker)) > 0
        and length(trim(subject)) > 0 and length(trim(source_system)) > 0
    ),
    constraint corporate_action_ticker_change_authority_chk check (
        event_type <> 'TICKER_CHANGE' or authority = 'OFFICIAL_BORSA_LINEAGE'
    )
);

create table zk.corporate_action_covered_windows (
    window_id text primary key,
    start_at timestamptz not null,
    end_at timestamptz not null,
    complete boolean not null,
    source_manifest_sha256 text not null,
    created_at timestamptz not null default now(),
    constraint corporate_action_window_time_chk check (start_at <= end_at),
    constraint corporate_action_window_hash_chk check (
        source_manifest_sha256 ~ '^[0-9a-f]{64}$'
    )
);

create function zk.reject_corporate_action_bootstrap_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'corporate-action bootstrap records are append-only';
end;
$fn$;

create trigger corporate_action_evidence_immutable_trg
before update or delete on zk.corporate_action_evidence
for each row execute function zk.reject_corporate_action_bootstrap_mutation();

create trigger corporate_action_windows_immutable_trg
before update or delete on zk.corporate_action_covered_windows
for each row execute function zk.reject_corporate_action_bootstrap_mutation();
