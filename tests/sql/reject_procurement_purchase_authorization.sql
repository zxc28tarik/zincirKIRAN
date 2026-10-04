\set ON_ERROR_STOP on
insert into zk.procurement_specs (
 specification_id,definition_version,preregistered_at,purchase_authorized
) values ('reject-buy','v1',now(),true);
