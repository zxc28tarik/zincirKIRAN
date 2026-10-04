set -e
run_reject_guard() {
  file="$1"; label="$2"
  if psql -v ON_ERROR_STOP=1 -f "$file"; then
    echo "$label was incorrectly accepted"; exit 1
  else
    echo "$label correctly rejected"
  fi
}
run_reject_guard tests/sql/reject_evidence_spec_mutation.sql "Evidence readiness spec mutation"
run_reject_guard tests/sql/reject_conflicting_source_artifact.sql "Conflicting logical source artifact"
run_reject_guard tests/sql/reject_evidence_snapshot_before_prereg.sql "Snapshot before preregistration"
run_reject_guard tests/sql/reject_invalid_evidence_coverage.sql "Invalid evidence coverage"
