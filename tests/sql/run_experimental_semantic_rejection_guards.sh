set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_experimental_semantic_authority_upgrade.sql "Experimental semantic authority upgrade"
run_reject_guard tests/sql/reject_experimental_semantic_authoritative_flag.sql "Experimental semantic authoritative flag"
run_reject_guard tests/sql/reject_experimental_semantic_mutation.sql "Experimental semantic mutation"
