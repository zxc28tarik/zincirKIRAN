set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_experimental_factor_dataset_promotion.sql "Experimental dataset promotion"
run_reject_guard tests/sql/reject_experimental_factor_dataset_production.sql "Experimental dataset production flag"
run_reject_guard tests/sql/reject_experimental_factor_dataset_mutation.sql "Experimental dataset mutation"
run_reject_guard tests/sql/reject_experimental_factor_bad_label_spec.sql "Experimental label calendar shortcut"
