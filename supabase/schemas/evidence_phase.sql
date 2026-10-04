-- Zincir Kıran — Evidence Phase / Real PIT Snapshot schema v0.1
-- Real source artifacts and readiness manifests. Append-only; no neutral fill.

create table zk.evidence_readiness_specs (
    specification_id text not null,
    definition_version text not null,
    preregistered_at timestamptz not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint evidence_readiness_spec_text_chk check (
        length(trim(specification_id)) > 0
        and length(trim(definition_version)) > 0
    )
);

create function zk.reject_evidence_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'evidence-phase records are append-only';
end;
$fn$;

create trigger evidence_readiness_specs_immutable_trg
before update or delete on zk.evidence_readiness_specs
for each row execute function zk.reject_evidence_mutation();

create table zk.evidence_readiness_thresholds (
    specification_id text not null,
    definition_version text not null,
    domain text not null,
    minimum_coverage numeric not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, domain),
    foreign key (specification_id, definition_version)
        references zk.evidence_readiness_specs(specification_id, definition_version),
    constraint evidence_threshold_domain_chk check (
        domain in (
            'PRICES','VOLUME','FINANCIALS','PUBLICATION_TIMESTAMPS',
            'CORPORATE_ACTIONS','UNIVERSE_HISTORY'
        )
    ),
    constraint evidence_threshold_coverage_chk check (
        minimum_coverage between 0 and 1
    )
);

create trigger evidence_readiness_thresholds_immutable_trg
before update or delete on zk.evidence_readiness_thresholds
for each row execute function zk.reject_evidence_mutation();

create table zk.source_artifacts (
    artifact_id text primary key,
    source_id text not null,
    source_url text not null,
    domain text not null,
    retrieved_at timestamptz not null,
    source_published_at timestamptz,
    content_sha256 text not null,
    byte_size bigint not null,
    logical_key text not null,
    created_at timestamptz not null default now(),
    unique (logical_key, content_sha256),
    constraint source_artifact_domain_chk check (
        domain in (
            'PRICES','VOLUME','FINANCIALS','PUBLICATION_TIMESTAMPS',
            'CORPORATE_ACTIONS','UNIVERSE_HISTORY'
        )
    ),
    constraint source_artifact_time_chk check (
        source_published_at is null or source_published_at <= retrieved_at
    ),
    constraint source_artifact_size_chk check (byte_size >= 0),
    constraint source_artifact_hash_chk check (
        content_sha256 ~ '^[0-9a-f]{64}$'
    ),
    constraint source_artifact_text_chk check (
        length(trim(artifact_id)) > 0
        and length(trim(source_id)) > 0
        and length(trim(source_url)) > 0
        and length(trim(logical_key)) > 0
    )
);

create function zk.reject_conflicting_source_artifact()
returns trigger language plpgsql as $fn$
begin
    if exists (
        select 1
          from zk.source_artifacts a
         where a.logical_key = new.logical_key
           and a.content_sha256 <> new.content_sha256
    ) then
        raise exception 'conflicting content for logical source artifact';
    end if;
    return new;
end;
$fn$;

create trigger source_artifacts_conflict_trg
before insert on zk.source_artifacts
for each row execute function zk.reject_conflicting_source_artifact();

create trigger source_artifacts_immutable_trg
before update or delete on zk.source_artifacts
for each row execute function zk.reject_evidence_mutation();

create table zk.pit_dataset_snapshots (
    snapshot_id text primary key,
    specification_id text not null,
    definition_version text not null,
    as_of timestamptz not null,
    created_at timestamptz not null,
    readiness text not null,
    manifest_sha256 text not null,
    recorded_at timestamptz not null default now(),
    foreign key (specification_id, definition_version)
        references zk.evidence_readiness_specs(specification_id, definition_version),
    constraint pit_snapshot_time_chk check (created_at >= as_of),
    constraint pit_snapshot_readiness_chk check (
        readiness in ('TOURNAMENT_READY','BLOCKED_WITH_GAPS')
    ),
    constraint pit_snapshot_hash_chk check (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    constraint pit_snapshot_text_chk check (length(trim(snapshot_id)) > 0)
);

create function zk.validate_pit_dataset_snapshot()
returns trigger language plpgsql as $fn$
declare
    prereg timestamptz;
begin
    select preregistered_at into prereg
      from zk.evidence_readiness_specs
     where specification_id = new.specification_id
       and definition_version = new.definition_version;

    if new.created_at <= prereg then
        raise exception 'snapshot creation must follow readiness preregistration';
    end if;
    return new;
end;
$fn$;

create trigger pit_dataset_snapshots_validate_trg
before insert on zk.pit_dataset_snapshots
for each row execute function zk.validate_pit_dataset_snapshot();

create trigger pit_dataset_snapshots_immutable_trg
before update or delete on zk.pit_dataset_snapshots
for each row execute function zk.reject_evidence_mutation();

create table zk.pit_snapshot_artifacts (
    snapshot_id text not null references zk.pit_dataset_snapshots(snapshot_id),
    artifact_id text not null references zk.source_artifacts(artifact_id),
    created_at timestamptz not null default now(),
    primary key (snapshot_id, artifact_id)
);

create trigger pit_snapshot_artifacts_immutable_trg
before update or delete on zk.pit_snapshot_artifacts
for each row execute function zk.reject_evidence_mutation();

create table zk.pit_snapshot_domain_coverage (
    snapshot_id text not null references zk.pit_dataset_snapshots(snapshot_id),
    domain text not null,
    observed_securities integer not null,
    required_securities integer not null,
    observed_periods integer not null,
    required_periods integer not null,
    created_at timestamptz not null default now(),
    primary key (snapshot_id, domain),
    constraint pit_snapshot_coverage_domain_chk check (
        domain in (
            'PRICES','VOLUME','FINANCIALS','PUBLICATION_TIMESTAMPS',
            'CORPORATE_ACTIONS','UNIVERSE_HISTORY'
        )
    ),
    constraint pit_snapshot_coverage_nonnegative_chk check (
        observed_securities >= 0
        and required_securities >= 0
        and observed_periods >= 0
        and required_periods >= 0
        and observed_securities <= required_securities
        and observed_periods <= required_periods
    )
);

create trigger pit_snapshot_domain_coverage_immutable_trg
before update or delete on zk.pit_snapshot_domain_coverage
for each row execute function zk.reject_evidence_mutation();

create table zk.pit_snapshot_gaps (
    snapshot_id text not null references zk.pit_dataset_snapshots(snapshot_id),
    gap_reason text not null,
    created_at timestamptz not null default now(),
    primary key (snapshot_id, gap_reason),
    constraint pit_snapshot_gap_text_chk check (length(trim(gap_reason)) > 0)
);

create trigger pit_snapshot_gaps_immutable_trg
before update or delete on zk.pit_snapshot_gaps
for each row execute function zk.reject_evidence_mutation();

create function zk.audit_snapshot_readiness()
returns trigger language plpgsql as $fn$
declare
    missing_count integer;
begin
    if new.readiness = 'TOURNAMENT_READY' then
        select count(*) into missing_count
          from zk.evidence_readiness_thresholds t
         where t.specification_id = new.specification_id
           and t.definition_version = new.definition_version
           and not exists (
               select 1
                 from zk.pit_snapshot_domain_coverage c
                where c.snapshot_id = new.snapshot_id
                  and c.domain = t.domain
           );

        if missing_count > 0 then
            raise exception 'tournament-ready snapshot is missing required domain coverage';
        end if;
    end if;
    return new;
end;
$fn$;
