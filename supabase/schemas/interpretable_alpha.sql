-- Zincir Kıran — Interpretable Alpha v1 aggregation specification schema

create table zk.alpha_aggregation_specs (
    specification_id text not null,
    definition_version text not null,
    horizon_days integer not null,
    aggregation_rule_id text not null,
    normalization_rule_id text not null,
    weight_policy_id text not null,
    coverage_rule_id text not null,
    parameters jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    primary key (specification_id, definition_version),
    constraint alpha_aggregation_horizon_chk
        check (horizon_days in (20, 60, 120, 252)),
    constraint alpha_aggregation_text_chk
        check (
            length(trim(specification_id)) > 0
            and length(trim(definition_version)) > 0
            and length(trim(aggregation_rule_id)) > 0
            and length(trim(normalization_rule_id)) > 0
            and length(trim(weight_policy_id)) > 0
            and length(trim(coverage_rule_id)) > 0
        ),
    constraint alpha_aggregation_parameters_chk
        check (jsonb_typeof(parameters) = 'object')
);

create function zk.reject_alpha_aggregation_mutation()
returns trigger
language plpgsql
as $$
begin
    raise exception 'alpha aggregation specifications are append-only';
end;
$$;

create trigger alpha_aggregation_specs_immutable_trg
before update or delete on zk.alpha_aggregation_specs
for each row execute function zk.reject_alpha_aggregation_mutation();
