-- Zincir Kıran — Official Source Acquisition schema v0.1
-- Records real acquisition attempts and exact artifact receipts. Append-only.

create table zk.official_source_definitions (
    source_id text primary key,
    name text not null,
    landing_url text not null,
    official boolean not null,
    historical_access_note text not null,
    runtime_dependency_allowed boolean not null,
    created_at timestamptz not null default now(),
    constraint official_source_text_chk check (
        length(trim(source_id)) > 0
        and length(trim(name)) > 0
        and length(trim(landing_url)) > 0
        and length(trim(historical_access_note)) > 0
    )
);

create function zk.reject_official_acquisition_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'official acquisition records are append-only';
end;
$fn$;

create trigger official_source_definitions_immutable_trg
before update or delete on zk.official_source_definitions
for each row execute function zk.reject_official_acquisition_mutation();

create table zk.acquisition_attempts (
    acquisition_id text primary key,
    source_id text not null references zk.official_source_definitions(source_id),
    requested_url text not null,
    attempted_at timestamptz not null,
    status text not null,
    blocker_code text,
    blocker_detail text,
    created_at timestamptz not null default now(),
    constraint acquisition_status_chk check (
        status in ('ACQUIRED','BLOCKED','MANUAL_EXPORT_REQUIRED')
    ),
    constraint acquisition_blocker_chk check (
        (
            status = 'ACQUIRED'
            and blocker_code is null
            and blocker_detail is null
        )
        or (
            status <> 'ACQUIRED'
            and blocker_code is not null
            and blocker_detail is not null
            and length(trim(blocker_code)) > 0
            and length(trim(blocker_detail)) > 0
        )
    ),
    constraint acquisition_text_chk check (
        length(trim(acquisition_id)) > 0
        and length(trim(requested_url)) > 0
    )
);

create trigger acquisition_attempts_immutable_trg
before update or delete on zk.acquisition_attempts
for each row execute function zk.reject_official_acquisition_mutation();

create table zk.acquired_artifact_receipts (
    acquisition_id text primary key references zk.acquisition_attempts(acquisition_id),
    source_id text not null references zk.official_source_definitions(source_id),
    source_url text not null,
    retrieved_at timestamptz not null,
    content_sha256 text not null,
    byte_size bigint not null,
    media_type text,
    created_at timestamptz not null default now(),
    constraint acquired_artifact_hash_chk check (
        content_sha256 ~ '^[0-9a-f]{64}$'
    ),
    constraint acquired_artifact_size_chk check (byte_size >= 0),
    constraint acquired_artifact_text_chk check (
        length(trim(source_url)) > 0
    )
);

create function zk.validate_acquired_artifact_receipt()
returns trigger language plpgsql as $fn$
declare
    attempt_status text;
    attempt_source text;
begin
    select status, source_id into attempt_status, attempt_source
      from zk.acquisition_attempts
     where acquisition_id = new.acquisition_id;

    if attempt_status <> 'ACQUIRED' then
        raise exception 'artifact receipt requires ACQUIRED attempt';
    end if;

    if attempt_source <> new.source_id then
        raise exception 'artifact receipt source mismatch';
    end if;

    return new;
end;
$fn$;

create trigger acquired_artifact_receipts_validate_trg
before insert on zk.acquired_artifact_receipts
for each row execute function zk.validate_acquired_artifact_receipt();

create trigger acquired_artifact_receipts_immutable_trg
before update or delete on zk.acquired_artifact_receipts
for each row execute function zk.reject_official_acquisition_mutation();
