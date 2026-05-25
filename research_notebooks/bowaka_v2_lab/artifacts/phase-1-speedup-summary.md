# Phase 1 — objective_minimal artifact mode

Speedup report §5.1 / §10.1 / §11.2 (matrix doc §8.4).

## What landed

- **`run_backtest(..., artifact_mode="full" | "objective_minimal")`**
  parameter added to `sim/backtester.py`. Default `"full"` preserves every
  existing call site verbatim — every artifact in `_REQUIRED_ARTIFACTS`
  still lands on disk. In `"objective_minimal"` mode the simulator runs the
  full event loop / portfolio / fill driver / exit driver / daily-equity
  collection / execution-quality build / exit-analysis build / finalize
  quote-coverage gate IDENTICALLY, but suppresses every disk write:
  `run_manifest.json`, `config_snapshot.json`, `dataset_manifest.json`,
  `code_manifest.json`, `candidate_events.{jsonl,parquet}`,
  `gate_dump.parquet` (+ partitioned), `entry_decisions.parquet`,
  `orders.parquet`, `fills.parquet`, `positions.parquet`,
  `trades.parquet`, `daily_equity.parquet`,
  `execution_quality.parquet`, `events/events.parquet` (+ partitioned),
  `exit_analysis.json`, `summary.json`, the (rewritten)
  `data_quality_report.json`, `report.md`, `report.json`, the parity
  diff yaml, the per-session universe artifacts (snapshot parquet +
  funnel json), and the promotion checklist / suitability decision. The
  intended_realism unannotated-parity-diff and finalize quote-coverage
  gates still fire (correctness, not artifacts).
- **`BacktestResult` enrichment.** Added the in-memory fields the objective
  consumes: `daily_equity`, `execution_quality_rows`,
  `quote_coverage_rows`, `orders`, `fills`, `positions`, `exit_analysis`,
  `profile_counters`, `artifact_mode`. Populated in both modes.
- **`fold_result_from_backtest_result(fold_id, result)`** added to
  `optuna/objective.py` — mirrors `fold_result_from_report` exactly. The
  drawdown comes from `result.daily_equity` (mark-to-market), the
  fill_rate / quote_coverage / missing_quote_count lookup prefers
  `execution_quality_rows` then falls back to `summary`.
- **`_run_fold_backtest_objective`** added to
  `optuna/walkforward_runner.py`. Same PIT universe / daily cache /
  suppliers as `_run_fold_backtest`, only difference is the
  `artifact_mode="objective_minimal"` flag. Returns the in-memory
  `BacktestResult` for the converter.
- **`_run_validation_folds` + `make_walkforward_objective`** now accept
  `objective_artifact_mode: str = "full"` and dispatch to the appropriate
  fold runner + converter. The neighbor-rerun path in
  `build_best_trial_report` and `score_final_holdout` stay on **full
  mode** (audit trail).
- **`OptunaConfig.objective_artifact_mode: Literal["full",
  "objective_minimal"] = "full"`** added to the schema and the
  config generator. The 3 generated optuna configs
  (`bowaka_v2_actual_iex_{current_code,intended_realism}_optuna.yml`,
  `bowaka_v2_actual_sip_intended_realism_optuna.yml`) carry the flag with
  default `full`. Phase 5 flips them to `objective_minimal`.
- **`universe/persist.py::compute_universe_hashes`** added — same hashes
  as `write_universe_artifacts` but without the parquet/json writes; used
  by `objective_minimal` for the run-manifest extras.
- **In-memory parity-diff path.** `config/config_diff.py::build_config_diff`
  is reused directly in objective_minimal mode so the realism
  unannotated-mismatch gate still fires (without writing the diff yaml).

## New tests

- `tests/unit/optuna/test_fold_result_from_backtest_result.py` (5 tests).
- `tests/unit/sim/test_backtest_full_mode_unchanged.py` (2 tests).
- `tests/integration/test_objective_minimal_parity.py` (4 tests).
- `tests/integration/test_objective_minimal_walkforward.py` (1 test).

## Result

`make test` (full unit + parity + integration + reconcile, excluding
slow/live): **1166 passed, 0 failed, 12 deselected** (14:25).

## Branch

`feature/phase-1-objective-minimal` merged to `dev` with `--no-ff`.
Phase 2 takes off from `dev` next.
