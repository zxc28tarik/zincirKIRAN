-- Zincir Kıran — First Experimental Factor Materialization schema v0.1

create table zk.experimental_factor_definitions (
    factor_id text not null,
    definition_version text not null,
    economic_family text not null,
    specification text not null,
    expected_direction text not null,
    authority text not null default 'EXPERIMENTAL_VERSION_RISK',
    production_eligible boolean not null default false,
    created_at timestamptz not null default now(),
    primary key (factor_id, definition_version),
    constraint experimental_factor_definition_direction_chk check (
        expected_direction in ('HIGHER_IS_BETTER','LOWER_IS_BETTER')
    ),
    constraint experimental_factor_definition_authority_chk check (
        authority = 'EXPERIMENTAL_VERSION_RISK'
    ),
    constraint experimental_factor_definition_no_prod_chk check (
        production_eligible = false
    ),
    constraint experimental_factor_definition_text_chk check (
        length(trim(factor_id)) > 0
        and length(trim(definition_version)) > 0
        and length(trim(economic_family)) > 0
        and length(trim(specification)) > 0
    )
);

create function zk.reject_experimental_factor_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'experimental factor records are append-only';
end;
$fn$;

create trigger experimental_factor_definitions_immutable_trg
before update or delete on zk.experimental_factor_definitions
for each row execute function zk.reject_experimental_factor_mutation();

create table zk.experimental_factor_values (
    dataset_id text not null,
    factor_id text not null,
    definition_version text not null,
    security_id text not null,
    as_of date not null,
    value numeric,
    unavailable_reason text,
    authority text not null default 'EXPERIMENTAL_VERSION_RISK',
    created_at timestamptz not null default now(),
    primary key (dataset_id, factor_id, definition_version, security_id, as_of),
    foreign key (factor_id, definition_version)
        references zk.experimental_factor_definitions(factor_id, definition_version),
    constraint experimental_factor_value_authority_chk check (
        authority = 'EXPERIMENTAL_VERSION_RISK'
    ),
    constraint experimental_factor_value_missing_chk check (
        (value is not null and unavailable_reason is null)
        or (value is null and unavailable_reason is not null and length(trim(unavailable_reason)) > 0)
    ),
    constraint experimental_factor_value_finite_chk check (
        value is null or value not in ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
    )
);

create trigger experimental_factor_values_immutable_trg
before update or delete on zk.experimental_factor_values
for each row execute function zk.reject_experimental_factor_mutation();

create function zk.require_experimental_factor_authority(
    p_factor_id text,
    p_definition_version text,
    p_requested_authority text
)
returns void
language plpgsql
as $fn$
declare
    auth text;
begin
    select authority into auth
      from zk.experimental_factor_definitions
     where factor_id = p_factor_id
       and definition_version = p_definition_version;

    if auth is null then
        raise exception 'experimental factor definition is not registered';
    end if;
    if p_requested_authority <> 'EXPERIMENTAL_VERSION_RISK' then
        raise exception 'experimental factor cannot be promoted to authoritative evidence';
    end if;
end;
$fn$;
