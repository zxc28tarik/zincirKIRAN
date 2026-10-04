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

run_reject_guard tests/sql/reject_portfolio_spec_mutation.sql "Portfolio specification mutation"
run_reject_guard tests/sql/reject_portfolio_production_promotion.sql "Portfolio production promotion"
run_reject_guard tests/sql/reject_late_preregistered_portfolio_run.sql "Post-hoc portfolio protocol"
run_reject_guard tests/sql/reject_portfolio_candidate_source_mutation.sql "Portfolio candidate source mutation"
run_reject_guard tests/sql/reject_ineligible_portfolio_target.sql "Ineligible portfolio target"
run_reject_guard tests/sql/reject_future_portfolio_execution_evidence.sql "Future portfolio execution evidence"
run_reject_guard tests/sql/reject_stale_portfolio_order.sql "Stale portfolio order evidence"
run_reject_guard tests/sql/reject_portfolio_capacity_order.sql "Capacity-exceeding portfolio order"
run_reject_guard tests/sql/reject_portfolio_cost_arithmetic.sql "Invalid portfolio cost arithmetic"
run_reject_guard tests/sql/reject_portfolio_sizing_mismatch.sql "Portfolio sizing mismatch"
run_reject_guard tests/sql/reject_missing_portfolio_liquidity_bypass.sql "Missing portfolio liquidity bypass"
run_reject_guard tests/sql/reject_portfolio_constraint_relaxation.sql "Portfolio constraint relaxation"
run_reject_guard tests/sql/reject_incomplete_portfolio_run.sql "Incomplete portfolio run"
run_reject_guard tests/sql/reject_posthoc_portfolio_reason.sql "Post-hoc portfolio child mutation"
