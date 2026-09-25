\set ON_ERROR_STOP on

do $$
begin
    if to_regclass('zk.feature_applicability') is null then
        raise exception 'zk.feature_applicability does not exist';
    end if;

    if not exists (
        select 1
        from pg_constraint
        where conname = 'financial_facts_restatement_status_chk'
    ) then
        raise exception 'financial facts restatement constraint missing';
    end if;
end
$$;

insert into zk.feature_applicability (
    feature_id,
    company_type,
    decision_version,
    applicability_state,
    rationale
) values (
    'example_feature',
    'EXAMPLE_TYPE',
    'v1',
    'UNDECIDED',
    'smoke test only'
);

select applicability_state
from zk.feature_applicability
where feature_id = 'example_feature'
  and company_type = 'EXAMPLE_TYPE'
  and decision_version = 'v1';
