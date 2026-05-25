# Phase 2 — Precomputed FoldRuntimeContext

Speedup report §5.2 / §10.2 / §11.2.

## What landed

- **`optuna/fold_context.py`** (new): `FoldRuntimeContext` frozen dataclass +
  `FoldSupplierBundle` + `CONTEXT_AFFECTING_PREFIXES` constant +
  `assert_search_space_does_not_affect_context()` guard +
  `build_fold_contexts()` (per-split) + `build_holdout_context()`.
  Each context caches: `sessions` (half-open), `scan_times_by_session`,
  `universe_by_session` (PIT), `eligible_symbols_by_session`,
  `daily_cache_by_session`, and the four per-fold supplier callables
  (`minute`, `daily`, `quote`, `forward_minute`). The dataclass is frozen
  so trials cannot mutate shared state.
- **Search-space guard.** Any tunable parameter whose name starts with
  `universe.`, `historical_features.`, `market_data.`, `data.`,
  `session.scanner_start`, `session.scanner_end`,
  `session.scan_interval_seconds`, or `simulation.intraday_window_policy`
  raises `OptunaStudyInvalidError` — these inputs feed the precomputed
  cache, so tuning them would silently invalidate it. The default search
  space passes.
- **`walkforward_runner.py`:**
  - `_run_fold_backtest(..., ctx=None)` — new optional `ctx` parameter.
    When supplied, sessions / PIT universe / daily cache / suppliers
    come from the precomputed context. The legacy (no-ctx) path is
    preserved unchanged.
  - `_run_fold_backtest_objective(..., ctx=None)` — same treatment.
  - `_run_validation_folds(..., fold_contexts=None)` — threads the
    per-split contexts to both inner runners.
  - `make_walkforward_objective(..., fold_contexts=None)` — forwards to
    `_run_validation_folds`.
  - `build_best_trial_report(..., fold_contexts=None)` — neighbor reruns
    reuse the precomputed contexts (full artifact mode still applies).
  - `run_walkforward_study(...)` — calls
    `assert_search_space_does_not_affect_context(...)` then
    `build_fold_contexts(...)` ONCE before the objective and threads
    them through `make_walkforward_objective` and
    `build_best_trial_report`.
- **`optuna/holdout.py::score_final_holdout`** — builds the holdout
  context via `build_holdout_context(...)` and passes it to
  `_run_fold_backtest(..., ctx=...)` so the holdout uses the same
  precomputed-cache path as validation.

## New tests

- `tests/unit/optuna/test_context_affecting_search_space_guard.py` (13).
- `tests/unit/optuna/test_fold_context_invariants.py` (5).
- `tests/integration/test_fold_context_parity.py` (3).
- `tests/integration/test_fold_context_no_mutation.py` (1).

## Result

`make test` (full unit + parity + integration + reconcile, excluding
slow/live): **1188 passed, 0 failed, 12 deselected** (15:13).

## Branch

`feature/phase-2-fold-runtime-context` merged to `dev` with `--no-ff`.
Phase 3 takes off from `dev` next.
