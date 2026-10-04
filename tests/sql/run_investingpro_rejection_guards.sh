set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_investingpro_100_rows.sql "InvestingPro 100-row export"
run_reject_guard tests/sql/reject_investingpro_current_backfill.sql "InvestingPro current estimate historical backfill"
run_reject_guard tests/sql/reject_investingpro_mutation.sql "InvestingPro record mutation"
