set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_official_source_mutation.sql "Official source mutation"
run_reject_guard tests/sql/reject_blocked_acquisition_without_reason.sql "Blocked acquisition without reason"
run_reject_guard tests/sql/reject_receipt_for_blocked_acquisition.sql "Receipt for blocked acquisition"
