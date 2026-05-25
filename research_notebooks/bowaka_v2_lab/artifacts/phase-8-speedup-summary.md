# Phase 8 — Scan feature-matrix precompute builder + manifest (default off)

Speedup report §6.4 / matrix doc §5–§10, §12, §17.

## What landed

- **`scanner/scan_matrix.py`** (new):
  * Column schemas:
    `DYNAMIC_FLOAT64_COLUMNS` (16 cells: session OHL + last price + volume
    + range + volume-curve fraction + expected/realized volumes + rvol +
    range expansion + close location + EMA distance + current return + gap
    + bar age),
    `DYNAMIC_INT64_COLUMNS` (1: last_bar_ts_ns, sentinel `-1`),
    `DYNAMIC_UINT8_COLUMNS` (4: has_bar, has_baseline, has_valid_timestamp,
    bar_timestamp_was_naive),
    `STATIC_FLOAT64_COLUMNS` (8 daily-baseline values),
    `STATIC_INT8_COLUMNS` (4 venue / class / eligibility codes).
  * `ScanMatrixManifest` frozen dataclass (matrix doc §8.1): matrix_id,
    matrix_version, config_input_hash, dataset_hash, feed, scope,
    created_at_utc, reserved_system_gib, max_optuna_workers, sessions,
    columns, bowaka_lab_version, code_hashes.
  * `ScanMatrixSession` frozen dataclass — read-only view over the
    session's memmap arrays + universe_meta.
  * `ScanMatrixStore(root, *, readonly, holdout_window)`:
    `open_session(date, *, purpose)` with the holdout-isolation guard
    (`HoldoutMatrixReadError` for objective reads of any session
    inside the holdout window; `purpose="final_holdout"` opts in).
  * `compute_matrix_input_hash(cfg, plan, sessions_by_scope, *,
    source_root, dataset_hash)` — SHA-256 over the matrix-input cfg
    subset (feed, scanner cadence, intraday-window policy, universe
    filters, historical-features knobs, lake root, dataset hash, plus
    the source-file hashes for the feature/scheduler/universe modules).
    Stable under signals/sizing/risk/execution/exits changes —
    matrix is reusable across trials.
  * `MATRIX_SENSITIVE_PREFIXES` + `assert_search_space_compatible_with_matrix()`
    — raises `OptunaStudyInvalidError` for any search-space key that
    would invalidate the precomputed matrix.
  * `build_session_partition(session_date, cfg, lake_root, feed, *,
    store_root, scope)` (Stage A: parity-first, slow):
    builds the PIT universe (falling back to `cfg.universe.symbols`
    when the lake has no asset master), loads each session's
    minute bars once, computes every dynamic feature per scan via
    `aggregate_forming_session_bar` + `compute_volume_curve_fraction`
    + `compute_forming_session_features`, writes `.npy` memmaps +
    `universe_meta.parquet` + `daily_baselines.parquet` to a `.tmp/`
    directory, SHA-256s every file into a session manifest, then
    atomically renames into place.
  * `build_scan_matrix(config_path, *, scope, workers, reserve_gib,
    max_optuna_workers, store_root)` builder driver:
    enumerates sessions for the scope via `calendar_sessions_half_open`,
    constructs a `MemoryBudget` from `reserve_gib` + `max_optuna_workers`,
    asserts launch safety against a coarse size estimate, builds each
    session partition (serial in Phase 8 — Phase 9 may parallelise via
    a `ProcessPoolExecutor` with the spawn worker bootstrap), then
    writes the top-level `manifest.json`.
  * `verify_scan_matrix(store_root, config_path, *, sample_count)`
    spot-checks a handful of `(session, symbol, scan)` cells against the
    matrix structure (presence + dtype + has_bar / last_price coherence).

- **CLI** (`bowaka-v2-lab scan-matrix build|verify`):
  Both subcommands honour `--workers`, `--reserve-system-gib`,
  `--max-optuna-workers`, `--store-root`, `--scope`. Build returns the
  store root + status JSON; verify exits 0 on ok/warn and prints a
  per-issue report.

- **`config.models.OptunaConfig.acceleration: dict[str, Any] = {}`**
  added. The 3 generated optuna configs carry the full
  `optuna.acceleration.scan_matrix` block with `enabled: false` —
  Phase 9 flips this on once the runtime evaluator parity is proven.

## New tests

- `tests/unit/scanner/test_scan_matrix_manifest_hash.py` (7).
- `tests/unit/scanner/test_scan_matrix_refuses_matrix_sensitive_search_space.py` (15).
- `tests/unit/scanner/test_scan_matrix_holdout_read_guard.py` (5).
- `tests/unit/scanner/test_scan_matrix_memory_budget_refuses_unsafe_plan.py` (3).
- `tests/unit/scanner/test_scan_matrix_stable_score_tie_order.py` (2).
- `tests/unit/scanner/test_scan_matrix_missing_value_gate_semantics.py` (4).
- `tests/integration/test_scan_matrix_feature_row_parity.py` (1):
  round-trip via `build_session_partition` → `ScanMatrixStore.open_session`.
- `tests/integration/test_scan_matrix_cli_build_verify.py` (1):
  end-to-end `scan-matrix build` + `scan-matrix verify` via the CLI.

## Result

`make test`: **1285 passed, 2 skipped, 12 deselected** (10:32). The 2
skipped are the Phase 5 PostgreSQL-gated tests.

## Branch

`feature/phase-8-scan-matrix-builder` merged to `dev` with `--no-ff`.
Phase 9 (matrix-backed scanner runtime) takes off from `dev` next.
