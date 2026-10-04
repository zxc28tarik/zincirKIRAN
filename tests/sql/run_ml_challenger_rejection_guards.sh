set -e

run_reject_guard() {
  file="$1"
  label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"
    exit 1
  else
    echo "$label correctly rejected"
  fi
}

run_reject_guard tests/sql/reject_ml_spec_mutation.sql "ML challenger specification mutation"
run_reject_guard tests/sql/reject_ml_future_feature.sql "Future ML feature evidence"
run_reject_guard tests/sql/reject_ml_future_target.sql "Future ML target evidence"
run_reject_guard tests/sql/reject_ml_unregistered_feature.sql "Unregistered ML feature"
run_reject_guard tests/sql/reject_ml_prediction_before_fit.sql "ML prediction before fit"
