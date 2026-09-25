\set ON_ERROR_STOP on

insert into zk.feature_applicability (
    feature_id, company_type, decision_version, applicability_state
) values (
    'bad_feature', 'TYPE_A', 'v1', 'NEUTRAL'
);
