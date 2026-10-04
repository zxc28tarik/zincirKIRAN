set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_cross_project_mutation.sql "Cross-project manifest mutation"
run_reject_guard tests/sql/reject_cross_project_noncanonical_pit.sql "Noncanonical cross-project PIT promotion"
run_reject_guard tests/sql/reject_cross_project_bad_commit.sql "Bad cross-project commit identity"
