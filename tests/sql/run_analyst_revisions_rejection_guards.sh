set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_analyst_current_backfill.sql "Current-only analyst revision backfill"
run_reject_guard tests/sql/reject_analyst_revision_reverse_time.sql "Reverse analyst revision"
run_reject_guard tests/sql/reject_analyst_estimate_mutation.sql "Analyst estimate mutation"
