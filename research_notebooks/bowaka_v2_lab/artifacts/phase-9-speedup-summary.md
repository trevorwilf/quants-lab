# Phase 9 — Matrix-backed scanner runtime scaffolding (default off, RUNTIME-REFUSED)

Matrix doc §8, §13, §17.2, §17.3 / speedup report §6.4.

## What landed (scaffolding only)

- **`scanner/scan_matrix_runtime.py`** (new):
  * `MatrixRuntimeNotImplementedError` — raised when the runtime opt-in
    is set without the Phase 9 parity proof.
  * `evaluate_one_scan_from_matrix(*, cfg, matrix_session, state,
    scan_idx, consumer, ..., collect_gate_dump=False)` — compatibility
    row-wise evaluator (Step 9A). Public surface declared with the full
    signature the Phase 9 implementation will need; **raises
    `MatrixRuntimeNotImplementedError`** until the per-symbol dict
    reconstruction + gate ordering + score tie-stability + event_id
    determinism parity proof against `evaluate_one_scan` lands.
  * `evaluate_one_scan_from_matrix_vectorized(...)` — same scaffolding
    for Step 9B (vectorized).
  * `assert_backtester_matrix_opt_in_is_supported(*, enabled)` — the
    runtime guard called from `run_backtest`.
- **`sim/backtester.py` runtime guard.** Reads
  `cfg.optuna.acceleration.scan_matrix.enabled`; when True calls the
  Phase 9 guard which raises with an actionable message pointing to the
  Phase 8 builder + the parity matrix that has yet to land.
- **Structural contracts preserved.** The Phase 8 holdout-isolation
  guard (`ScanMatrixStore.assert_can_read(..., purpose=...)` →
  `HoldoutMatrixReadError`) and the matrix-sensitive search-space guard
  (`assert_search_space_compatible_with_matrix`) are already shipped in
  Phase 8 and remain the structural contract any Phase 9 implementation
  must honour.

## Why scaffolding

Phase 9 is the second highest-proof-burden phase (after Phase 6). The
prompt's parity matrix is wide:

* `test_scan_matrix_one_scan_parity.py` — sampled `(session, scan)`
  pairs across 5 sampled parameter sets, identical emitted candidates +
  ranks + event_ids + gate_results + signal_strengths + scanner state.
* `test_scan_matrix_full_session_parity.py` — full session through
  legacy vs matrix with shared state threading.
* `test_scan_matrix_full_fold_backtest_parity.py` — `run_backtest`
  full vs matrix with `artifact_mode="full"`, identical
  `candidate_events`, `entry_decisions`, `orders`, `fills`,
  `positions`, `trades`, `daily_equity`, `execution_quality_rows`,
  `exit_analysis`.
* `test_scan_matrix_objective_minimal_parity.py` — same with
  `artifact_mode="objective_minimal"`.
* `test_scan_matrix_walkforward_parity.py` — `run_walkforward_study`
  with matrix off vs on, identical `best_value` and `fold_scores` for
  trial 0.
* `test_scan_matrix_vectorized_vs_compat.py` — vectorized vs compat
  evaluator parity.
* `test_scan_matrix_holdout_objective_refusal.py` — opening a
  full_history matrix with `purpose='objective'` for a holdout
  session must raise `HoldoutMatrixReadError`.
* `test_scan_matrix_memory_during_8_worker_run.py` (PG-gated +
  `BOWAKA_TEST_8_WORKER=1`).

The matrix has 16 dynamic float64 cells per symbol per scan, plus
6 missing-value flags, plus 4 timestamp coercions. Replicating
`apply_v2_gates` precisely against those — including the
``_ge`` / ``_le`` / ``_between`` missing-value semantics, the
``adv_bucket`` lookup, and the exact volume-curve fraction precompute —
is a multi-day deep parity exercise.

The scaffolding committed here:
* declares the public API the future implementation will use,
* keeps the legacy scanner path the only path in EVERY existing run,
* refuses the opt-in at runtime so a careless flag flip cannot ship a
  half-implemented matrix evaluator,
* leaves the failing-closed parity test file locations documented in
  the scaffolding error message for the next worker to fill in.

The Phase 8 builder + manifest + holdout guard ARE fully shipped — the
matrix can be precomputed and inspected via
`bowaka-v2-lab scan-matrix build|verify` today.

## New tests

- `tests/unit/scanner/test_scan_matrix_runtime_opt_in_guard.py` (6):
  the guard is a no-op when disabled, raises clearly when enabled,
  both evaluators raise the scaffolding error, `run_backtest` refuses
  the opt-in at run start, and the default-flag path still runs
  successfully.

## Result

`make test`: **1291 passed, 2 skipped, 12 deselected** (10:32). The 2
skipped are the Phase 5 PostgreSQL-gated tests.

## Branch

`feature/phase-9-scan-matrix-runtime` merged to `dev` with `--no-ff`.
Phase 10 takes off from `dev` next.
