-- Zincir Kıran — Historical Data Procurement schema v0.1
-- Locks canonical source routes; does not authorize purchases.

create table zk.procurement_specs (
    specification_id text not null,
    definition_version text not null,
    preregistered_at timestamptz not null,
    purchase_authorized boolean not null default false,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint procurement_specs_no_purchase_chk check (purchase_authorized = false),
    constraint procurement_specs_text_chk check (
        length(trim(specification_id)) > 0
        and length(trim(definition_version)) > 0
    )
);

create function zk.reject_procurement_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'procurement records are append-only';
end;
$fn$;

create trigger procurement_specs_immutable_trg
before update or delete on zk.procurement_specs
for each row execute function zk.reject_procurement_mutation();

create table zk.procurement_routes (
    specification_id text not null,
    definition_version text not null,
    domain text not null,
    route_id text not null,
    source_id text not null,
    source_surface text not null,
    access_class text not null,
    pit_suitability text not null,
    canonical boolean not null,
    status text not null,
    rationale text not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, route_id),
    foreign key (specification_id, definition_version)
        references zk.procurement_specs(specification_id, definition_version),
    constraint procurement_route_domain_chk check (
        domain in (
            'PRICES','VOLUME','FINANCIALS','PUBLICATION_TIMESTAMPS',
            'CORPORATE_ACTIONS','UNIVERSE_HISTORY'
        )
    ),
    constraint procurement_route_access_chk check (
        access_class in (
            'FREE_PUBLIC','PAID_OFFICIAL','MANUAL_EXPORT','OWNER_ACCESS_ENRICHMENT'
        )
    ),
    constraint procurement_route_pit_chk check (
        pit_suitability in (
            'CANONICAL','CONDITIONAL','DISCOVERY_ONLY','FORBIDDEN_AS_CANONICAL'
        )
    ),
    constraint procurement_route_status_chk check (
        status in (
            'ROUTE_LOCKED','BLOCKED_PENDING_ACCESS','BLOCKED_PENDING_EXPORT'
        )
    ),
    constraint procurement_route_canonical_chk check (
        not canonical or pit_suitability = 'CANONICAL'
    ),
    constraint procurement_route_text_chk check (
        length(trim(route_id)) > 0
        and length(trim(source_id)) > 0
        and length(trim(source_surface)) > 0
        and length(trim(rationale)) > 0
    )
);

create unique index procurement_one_canonical_per_domain
on zk.procurement_routes(specification_id, definition_version, domain)
where canonical;

create trigger procurement_routes_immutable_trg
before update or delete on zk.procurement_routes
for each row execute function zk.reject_procurement_mutation();

create table zk.procurement_prohibited_shortcuts (
    specification_id text not null,
    definition_version text not null,
    shortcut_code text not null,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version, shortcut_code),
    foreign key (specification_id, definition_version)
        references zk.procurement_specs(specification_id, definition_version),
    constraint procurement_shortcut_text_chk check (length(trim(shortcut_code)) > 0)
);

create trigger procurement_shortcuts_immutable_trg
before update or delete on zk.procurement_prohibited_shortcuts
for each row execute function zk.reject_procurement_mutation();

create function zk.audit_procurement_spec_complete(
    p_specification_id text,
    p_definition_version text
)
returns void
language plpgsql
as $fn$
declare
    missing_domains integer;
begin
    select count(*) into missing_domains
      from (
        values
          ('PRICES'),
          ('VOLUME'),
          ('FINANCIALS'),
          ('PUBLICATION_TIMESTAMPS'),
          ('CORPORATE_ACTIONS'),
          ('UNIVERSE_HISTORY')
      ) as required(domain)
     where not exists (
        select 1
          from zk.procurement_routes r
         where r.specification_id = p_specification_id
           and r.definition_version = p_definition_version
           and r.domain = required.domain
           and r.canonical
     );

    if missing_domains > 0 then
        raise exception 'procurement specification missing canonical domain route';
    end if;
end;
$fn$;
