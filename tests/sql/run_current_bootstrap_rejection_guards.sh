set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_current_bootstrap_mutation.sql "Current bootstrap mutation"
run_reject_guard tests/sql/reject_current_bootstrap_historical_use.sql "Current artifact historical backfill"
