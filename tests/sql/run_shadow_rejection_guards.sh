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

run_reject_guard tests/sql/reject_shadow_protocol_mutation.sql "Shadow protocol mutation"
run_reject_guard tests/sql/reject_shadow_backdated_run.sql "Backdated shadow run"
run_reject_guard tests/sql/reject_shadow_decision_mutation.sql "Shadow decision mutation"
run_reject_guard tests/sql/reject_shadow_no_signal_weight.sql "NO_SIGNAL portfolio intent"
run_reject_guard tests/sql/reject_shadow_premature_label.sql "Premature shadow realized label"
run_reject_guard tests/sql/reject_shadow_unregistered_horizon.sql "Unregistered shadow label horizon"
