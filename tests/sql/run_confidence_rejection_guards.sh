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

run_reject_guard tests/sql/reject_confidence_spec_mutation.sql "Confidence specification mutation"
run_reject_guard tests/sql/reject_confidence_production_promotion.sql "Confidence production promotion"
run_reject_guard tests/sql/reject_future_confidence_evidence.sql "Future confidence evidence"
run_reject_guard tests/sql/reject_stale_confidence_available.sql "Stale confidence evidence as available"
run_reject_guard tests/sql/reject_confidence_protocol_mismatch.sql "Confidence protocol mismatch"
run_reject_guard tests/sql/reject_late_preregistered_confidence_run.sql "Post-hoc confidence protocol"
run_reject_guard tests/sql/reject_confidence_alpha_mutation.sql "Confidence source Alpha mutation"
run_reject_guard tests/sql/reject_invalid_confidence_arithmetic.sql "Invalid confidence arithmetic"
run_reject_guard tests/sql/reject_invalid_confidence_decision.sql "Invalid confidence decision"
run_reject_guard tests/sql/reject_incomplete_confidence_run.sql "Incomplete confidence run"
run_reject_guard tests/sql/reject_confidence_reason_mismatch.sql "Confidence reason mismatch"
