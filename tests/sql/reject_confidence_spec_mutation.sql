\set ON_ERROR_STOP on
update zk.confidence_specs
set signal_eligibility_threshold = 0.99
where specification_id = 'confidence-smoke'
  and definition_version = 'v1';
