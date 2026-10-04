-- Zincir Kıran — KAP Bulk Financial Bootstrap schema v0.1

create table zk.kap_bulk_financial_archives (
    year integer not null,
    period text not null,
    period_code integer not null,
    filename text not null,
    download_url text not null,
    sha256 text not null,
    member_count integer not null,
    size_bytes bigint not null,
    exact_manifest_match boolean not null,
    authority text not null default 'RAW_EVIDENCE',
    created_at timestamptz not null default now(),
    primary key (year, period_code),
    constraint kap_bulk_period_chk check (period in ('3A','6A','9A','Y')),
    constraint kap_bulk_code_chk check (period_code in (1,2,3,4)),
    constraint kap_bulk_sha_chk check (sha256 ~ '^[0-9a-f]{64}$'),
    constraint kap_bulk_counts_chk check (member_count > 0 and size_bytes > 0),
    constraint kap_bulk_authority_chk check (authority = 'RAW_EVIDENCE'),
    constraint kap_bulk_url_chk check (
        download_url like 'https://kap.org.tr/tr/api/financialTable/download/%'
    )
);

create function zk.reject_kap_bulk_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'KAP bulk archive records are append-only';
end;
$fn$;

create trigger kap_bulk_financial_archives_immutable_trg
before update or delete on zk.kap_bulk_financial_archives
for each row execute function zk.reject_kap_bulk_mutation();

create function zk.reject_kap_bulk_as_authoritative_pit()
returns trigger language plpgsql as $fn$
begin
    if new.authority <> 'RAW_EVIDENCE' then
        raise exception 'current KAP bulk archive cannot be promoted to authoritative historical PIT';
    end if;
    return new;
end;
$fn$;

create trigger kap_bulk_financial_archives_authority_trg
before insert on zk.kap_bulk_financial_archives
for each row execute function zk.reject_kap_bulk_as_authoritative_pit();
