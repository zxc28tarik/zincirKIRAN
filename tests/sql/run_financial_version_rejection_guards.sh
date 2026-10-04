set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_authoritative_incomplete_chain.sql "Authoritative incomplete version chain"
run_reject_guard tests/sql/reject_bulk_latest_authoritative_use.sql "Bulk latest authoritative use"
run_reject_guard tests/sql/reject_financial_version_mutation.sql "Financial version mutation"
