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

run_reject_guard tests/sql/reject_tournament_spec_mutation.sql "Tournament specification mutation"
run_reject_guard tests/sql/reject_tournament_structure_after_run.sql "Post-hoc tournament structure change"
run_reject_guard tests/sql/reject_tournament_purge_violation.sql "Tournament purge violation"
run_reject_guard tests/sql/reject_tournament_overlap.sql "Tournament validation overlap"
run_reject_guard tests/sql/reject_tournament_embargo_violation.sql "Tournament embargo violation"
run_reject_guard tests/sql/reject_tournament_nonadvancing_train.sql "Tournament non-advancing train cutoff"
run_reject_guard tests/sql/reject_tournament_late_run.sql "Post-hoc tournament protocol"
run_reject_guard tests/sql/reject_tournament_missing_cost_model.sql "Missing tournament cost model"
run_reject_guard tests/sql/reject_tournament_missing_as_zero.sql "Missing tournament metric treated as zero"
run_reject_guard tests/sql/reject_tournament_wrong_paired_difference.sql "Wrong tournament paired difference"
run_reject_guard tests/sql/reject_tournament_wrong_qvalue.sql "Wrong tournament BH q-value"
run_reject_guard tests/sql/reject_tournament_auto_promotion.sql "Automatic tournament promotion"
run_reject_guard tests/sql/reject_incomplete_tournament_run.sql "Incomplete tournament run"
