set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_experimental_lab_promotion.sql "Experimental Factor-Lab promotion"
run_reject_guard tests/sql/reject_experimental_lab_before_prereg.sql "Factor-Lab execution before preregistration"
run_reject_guard tests/sql/reject_experimental_lab_period_mutation.sql "Factor-Lab period mutation"
run_reject_guard tests/sql/reject_experimental_lab_bad_unavailable.sql "Factor-Lab unavailable period without reason"
