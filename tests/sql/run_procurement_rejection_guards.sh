set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_procurement_spec_mutation.sql "Procurement spec mutation"
run_reject_guard tests/sql/reject_procurement_purchase_authorization.sql "Purchase authorization"
run_reject_guard tests/sql/reject_procurement_nonpit_canonical.sql "Non-PIT canonical route"
run_reject_guard tests/sql/reject_procurement_duplicate_canonical.sql "Duplicate canonical route"
