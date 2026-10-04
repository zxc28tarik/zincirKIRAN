set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_kap_bulk_mutation.sql "KAP bulk mutation"
run_reject_guard tests/sql/reject_kap_bulk_authority_upgrade.sql "KAP bulk PIT authority upgrade"
