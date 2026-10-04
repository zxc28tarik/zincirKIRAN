set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_experimental_factor_promotion.sql "Experimental factor promotion"
run_reject_guard tests/sql/reject_experimental_factor_neutral_missing.sql "Experimental factor missing-without-reason"
run_reject_guard tests/sql/reject_experimental_factor_mutation.sql "Experimental factor mutation"
run_reject_guard tests/sql/reject_experimental_factor_production.sql "Experimental factor production flag"
