-- Zincir Kıran — Experimental Factor-Lab Dataset schema v0.1

create table zk.experimental_factor_datasets (
    dataset_id text primary key,
    authority text not null,
    historical_cells integer not null,
    cells_with_visible_financial_facts integer not null,
    production_eligible boolean not null default false,
    created_at timestamptz not null default now(),
    constraint experimental_factor_dataset_authority_chk check (
        authority = 'EXPERIMENTAL_VERSION_RISK'
    ),
    constraint experimental_factor_dataset_no_prod_chk check (
        production_eligible = false
    ),
    constraint experimental_factor_dataset_coverage_chk check (
        historical_cells > 0
        and cells_with_visible_financial_facts between 0 and historical_cells
    )
);

create function zk.reject_experimental_factor_dataset_mutation()
returns trigger language plpgsql as $fn$
begin
    raise exception 'experimental factor dataset records are append-only';
end;
$fn$;

create trigger experimental_factor_datasets_immutable_trg
before update or delete on zk.experimental_factor_datasets
for each row execute function zk.reject_experimental_factor_dataset_mutation();

create table zk.experimental_factor_dataset_inputs (
    dataset_id text not null references zk.experimental_factor_datasets(dataset_id),
    artifact_id text not null,
    sha256 text not null,
    authority text not null,
    scope_note text not null,
    created_at timestamptz not null default now(),
    primary key (dataset_id, artifact_id),
    constraint experimental_factor_input_sha_chk check (sha256 ~ '^[0-9a-f]{64}$'),
    constraint experimental_factor_input_text_chk check (
        length(trim(authority)) > 0 and length(trim(scope_note)) > 0
    )
);

create trigger experimental_factor_dataset_inputs_immutable_trg
before update or delete on zk.experimental_factor_dataset_inputs
for each row execute function zk.reject_experimental_factor_dataset_mutation();

create table zk.experimental_factor_dataset_risks (
    dataset_id text not null references zk.experimental_factor_datasets(dataset_id),
    risk_id text not null,
    created_at timestamptz not null default now(),
    primary key (dataset_id, risk_id),
    constraint experimental_factor_dataset_risk_text_chk check (
        length(trim(risk_id)) > 0
    )
);

create trigger experimental_factor_dataset_risks_immutable_trg
before update or delete on zk.experimental_factor_dataset_risks
for each row execute function zk.reject_experimental_factor_dataset_mutation();

create table zk.experimental_forward_label_specs (
    dataset_id text not null references zk.experimental_factor_datasets(dataset_id),
    horizon_days integer not null,
    target text not null,
    calendar_basis text not null,
    missing_policy text not null,
    created_at timestamptz not null default now(),
    primary key (dataset_id, horizon_days),
    constraint experimental_forward_label_horizon_chk check (
        horizon_days in (20,60,120,252)
    ),
    constraint experimental_forward_label_target_chk check (
        target = 'future_market_relative_return'
    ),
    constraint experimental_forward_label_calendar_chk check (
        calendar_basis = 'EXACT_TRADING_DAY_INDEX'
    ),
    constraint experimental_forward_label_missing_chk check (
        missing_policy = 'UNAVAILABLE_NOT_ZERO'
    )
);

create trigger experimental_forward_label_specs_immutable_trg
before update or delete on zk.experimental_forward_label_specs
for each row execute function zk.reject_experimental_factor_dataset_mutation();

create function zk.require_experimental_factor_dataset(
    p_dataset_id text,
    p_requested_authority text
)
returns void
language plpgsql
as $fn$
declare
    auth text;
begin
    select authority into auth
      from zk.experimental_factor_datasets
     where dataset_id = p_dataset_id;

    if auth is null then
        raise exception 'experimental factor dataset is not registered';
    end if;
    if p_requested_authority <> 'EXPERIMENTAL_VERSION_RISK' then
        raise exception 'experimental factor dataset cannot be promoted to authoritative evidence';
    end if;
end;
$fn$;
