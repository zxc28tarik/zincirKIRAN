set -e

run_reject_guard() {
  file="$1"
  label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"
    exit 1
  else
    echo "$label correctly rejected"
  fi
}

run_reject_guard tests/sql/reject_context_spec_mutation.sql "Context specification mutation"
run_reject_guard tests/sql/reject_context_production_promotion.sql "Context production promotion"
run_reject_guard tests/sql/reject_future_context_regime.sql "Future context regime evidence"
run_reject_guard tests/sql/reject_stale_context_classification.sql "Stale regime classification"
run_reject_guard tests/sql/reject_context_protocol_mismatch.sql "Context protocol mismatch"
run_reject_guard tests/sql/reject_late_preregistered_context_run.sql "Post-hoc context protocol"
run_reject_guard tests/sql/reject_context_rule_outside_base_plan.sql "Context rule outside base Alpha plan"
run_reject_guard tests/sql/reject_invalid_context_contradiction.sql "Invalid contradiction result"
run_reject_guard tests/sql/reject_invalid_context_interaction.sql "Invalid interaction result"
run_reject_guard tests/sql/reject_incomplete_context_run.sql "Incomplete context run"
run_reject_guard tests/sql/reject_overlapping_regime_state.sql "Overlapping regime state interval"
