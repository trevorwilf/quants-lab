# Phase 5 — PostgreSQL process-parallel Optuna (8 workers default)

Speedup report §6.1 / §10.5 / §11.3 (matrix doc §8.5, §15).

## What landed

- **`optuna/parallel.py`** (new):
  `WorkerResult`, `WorkerSpec`, `_BLAS_THREAD_ENV_VARS`,
  `pin_blas_threads_to_one()`, `run_parallel_bowaka_optimization(...)`.
  Each worker is a `multiprocessing.get_context("spawn").Process` that:
  1. Pins BLAS threads to 1 **before** importing NumPy
     (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`,
     `NUMEXPR_NUM_THREADS`, `BLIS_NUM_THREADS`,
     `VECLIB_MAXIMUM_THREADS`).
  2. Loads the study from PostgreSQL storage.
  3. Rebuilds its objective from a dotted factory reference (no parent
     closure pickling).
  4. Runs `study.optimize(..., n_trials=worker_trials, n_jobs=1)`.
  5. Reports completed/pruned/failed counts in a `WorkerResult`.
  Memory reserve is checked before launching workers
  (`MemoryBudget.assert_available_reserve()`).

- **`optuna/dispatcher.py::run_bowaka_optimization_dispatch`** (new):
  Single entry point used by `run_walkforward_study`. Behaviour:
  * `n_jobs <= 1` → serial in-process `study.optimize`.
  * `n_jobs > 1` AND PostgreSQL storage → launches the parallel pool.
    Worker count capped at `memory_budget.max_optuna_workers` (default
    8). `MemoryBudget.assert_launch_safe(n_workers=..., feature_store_gib_estimate=...)`
    is asserted. Reloads the study from storage on success so the
    parent sees every worker's trials.
  * `n_jobs > 1` AND non-PostgreSQL → raises `OptunaStudyInvalidError`
    in strict mode; logs a warning and falls back to serial otherwise.

- **`optuna/walkforward_runner.py`:**
  - New module-level `make_walkforward_objective_for_worker(config_path,
    *, search_space_overrides, ...)` — the dotted factory the workers
    import. Reloads the config + rebuilds the per-fold contexts from
    scratch (one-shot cost amortized across that worker's trial slice).
    Default `objective_artifact_mode="objective_minimal"` and
    `cached_suppliers=True` to match Phase 5 actual-config defaults.
  - `run_walkforward_study` now routes the optimize call through
    `run_bowaka_optimization_dispatch(...)` with a `MemoryBudget` built
    from the config's `optuna.parallel` block.
- **`config.models.OptunaConfig.parallel: dict[str, Any]`** added.
- **Config generator + 3 generated optuna configs** flipped to the
  Phase 5 defaults:
  * `storage`: PostgreSQL default
    (`${OPTUNA_STORAGE:-postgresql+psycopg2://optuna:optuna@optuna-postgres:5432/optuna}`).
  * `n_jobs: 8` (capped at `max_workers` at runtime).
  * `objective_artifact_mode: objective_minimal` (Phase 1 parity proven).
  * `cached_suppliers: true` (Phase 3 parity proven).
  * `parallel: {memory_reserve_gib: 32, max_workers: 8, strict_parallel:
    false, blas_thread_pin: true}`.
  Smoke + quarantined configs stay serial / SQLite.

## New tests

- `tests/unit/optuna/test_parallel_postgres_required.py` (4).
- `tests/unit/optuna/test_parallel_worker_caps_at_8.py` (2).
- `tests/unit/optuna/test_blas_threads_pinned_in_worker.py` (2,
  includes a spawn subprocess that verifies the env vars).
- `tests/integration/test_parallel_memory_guard_aborts.py` (3).
- `tests/integration/test_parallel_smoke_two_workers_postgres.py` (1,
  gated by `BOWAKA_TEST_POSTGRES=1` — skipped without it).
- `tests/integration/test_parallel_vs_serial_best_params_close_enough.py`
  (1, gated by `BOWAKA_TEST_POSTGRES=1` — skipped without it).

## Result

`make test`: **1229 passed, 2 skipped, 12 deselected** (10:10). The 2
skipped are the PostgreSQL-gated tests.

## Branch

`feature/phase-5-parallel-optuna` merged to `dev` with `--no-ff`. Phase 6
takes off from `dev` next.
