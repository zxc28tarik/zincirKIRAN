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

run_reject_guard tests/sql/reject_production_gate_spec_mutation.sql "Production gate spec mutation"
run_reject_guard tests/sql/reject_production_gate_late_preregistration.sql "Production evaluation before preregistration"
run_reject_guard tests/sql/reject_production_gate_auto_deploy.sql "Automatic production deployment"
run_reject_guard tests/sql/reject_production_gate_missing_required_evidence.sql "Production eligibility with missing evidence"
run_reject_guard tests/sql/reject_production_gate_failed_integrity.sql "Production eligibility with failed integrity"
