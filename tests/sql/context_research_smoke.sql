\set ON_ERROR_STOP on

insert into zk.context_research_specs (
    specification_id, definition_version, horizon_days,
    base_alpha_specification_id, base_alpha_definition_version,
    context_protocol_id, universe_rule_version, hypothesis, success_criteria,
    preregistered_at
) values (
    'context-smoke', 'v1', 20,
    'alpha-engine-smoke', 'v1',
    'context-protocol-v1', 'universe-v1',
    'Explicit context may explain Alpha stability.',
    'Improve OOS robustness without hidden Alpha mutation.',
    timestamptz '2026-09-01 00:00:00+00'
);

insert into zk.context_regime_dimensions (
    specification_id, definition_version, dimension_id, max_age_days
) values
    ('context-smoke', 'v1', 'macro_axis', 40),
    ('context-smoke', 'v1', 'risk_axis', 10);

insert into zk.context_regime_state_rules (
    specification_id, definition_version, dimension_id, state_id,
    lower_inclusive, upper_exclusive
) values
    ('context-smoke', 'v1', 'macro_axis', 'state_low', null, 0.0),
    ('context-smoke', 'v1', 'macro_axis', 'state_high', 0.0, null),
    ('context-smoke', 'v1', 'risk_axis', 'state_quiet', null, 1.0),
    ('context-smoke', 'v1', 'risk_axis', 'state_stressed', 1.0, null);

insert into zk.context_contradiction_rules (
    specification_id, definition_version, rule_id,
    left_admission_id, right_admission_id, minimum_absolute_signal
) values (
    'context-smoke', 'v1', 'value-vs-momentum',
    'alpha-smoke-adm-value', 'alpha-smoke-adm-mom', 0.25
);

insert into zk.context_interaction_rules (
    specification_id, definition_version, rule_id,
    left_admission_id, right_admission_id
) values (
    'context-smoke', 'v1', 'value-x-momentum',
    'alpha-smoke-adm-value', 'alpha-smoke-adm-mom'
);

insert into zk.context_contradiction_regime_requirements (
    specification_id, definition_version, rule_id, dimension_id, state_id
) values (
    'context-smoke', 'v1', 'value-vs-momentum',
    'risk_axis', 'state_stressed'
);

insert into zk.context_interaction_regime_requirements (
    specification_id, definition_version, rule_id, dimension_id, state_id
) values (
    'context-smoke', 'v1', 'value-x-momentum',
    'macro_axis', 'state_high'
);

insert into zk.context_regime_observations (
    observation_id, dimension_id, context_protocol_id, raw_value,
    window_start, window_end, available_at, source_snapshot_id
) values
    (
        'context-obs-macro', 'macro_axis', 'context-protocol-v1', 1.0,
        timestamptz '2026-09-01 00:00:00+00',
        timestamptz '2026-10-03 00:00:00+00',
        timestamptz '2026-10-03 01:00:00+00',
        'source-macro'
    ),
    (
        'context-obs-risk', 'risk_axis', 'context-protocol-v1', 2.0,
        timestamptz '2026-09-20 00:00:00+00',
        timestamptz '2026-10-03 00:00:00+00',
        timestamptz '2026-10-03 01:00:00+00',
        'source-risk'
    );

begin;
insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-run-evaluated', 'context-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00', 'EVALUATED'
);

insert into zk.context_factor_signals (
    context_run_id, admission_id, normalized_signal_value
) values
    ('context-run-evaluated', 'alpha-smoke-adm-value', 0.8),
    ('context-run-evaluated', 'alpha-smoke-adm-mom', -0.6);

insert into zk.context_regime_results (
    context_run_id, dimension_id, availability, observation_id, state_id
) values
    ('context-run-evaluated', 'macro_axis', 'CLASSIFIED', 'context-obs-macro', 'state_high'),
    ('context-run-evaluated', 'risk_axis', 'CLASSIFIED', 'context-obs-risk', 'state_stressed');

insert into zk.context_contradiction_results (
    context_run_id, rule_id, left_signal, right_signal,
    regime_condition_met, is_contradiction
) values (
    'context-run-evaluated', 'value-vs-momentum',
    0.8, -0.6, true, true
);

insert into zk.context_interaction_results (
    context_run_id, rule_id, left_signal, right_signal,
    state, interaction_value
) values (
    'context-run-evaluated', 'value-x-momentum',
    0.8, -0.6, 'ACTIVE', -0.48
);
commit;

begin;
insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-run-regime-abstain', 'context-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00', 'ABSTAIN_INSUFFICIENT_REGIME'
);

insert into zk.context_regime_results (
    context_run_id, dimension_id, availability, observation_id, state_id
) values
    (
        'context-run-regime-abstain', 'macro_axis',
        'CLASSIFIED', 'context-obs-macro', 'state_high'
    ),
    (
        'context-run-regime-abstain', 'risk_axis',
        'MISSING', null, null
    );
commit;

begin;
insert into zk.context_runs (
    context_run_id, specification_id, definition_version,
    prediction_timestamp, status
) values (
    'context-run-signal-abstain', 'context-smoke', 'v1',
    timestamptz '2026-10-04 00:00:00+00',
    'ABSTAIN_INSUFFICIENT_FACTOR_SIGNALS'
);

insert into zk.context_factor_signals (
    context_run_id, admission_id, normalized_signal_value
) values (
    'context-run-signal-abstain', 'alpha-smoke-adm-value', 0.8
);

insert into zk.context_missing_factor_signals (
    context_run_id, admission_id
) values (
    'context-run-signal-abstain', 'alpha-smoke-adm-mom'
);

insert into zk.context_regime_results (
    context_run_id, dimension_id, availability, observation_id, state_id
) values
    (
        'context-run-signal-abstain', 'macro_axis',
        'CLASSIFIED', 'context-obs-macro', 'state_high'
    ),
    (
        'context-run-signal-abstain', 'risk_axis',
        'CLASSIFIED', 'context-obs-risk', 'state_stressed'
    );
commit;

select context_run_id, status
from zk.context_runs
where specification_id = 'context-smoke'
order by context_run_id;
