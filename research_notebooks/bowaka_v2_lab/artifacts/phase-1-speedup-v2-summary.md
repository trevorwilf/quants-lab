# Phase 1 — Exact batch daily-feature cache

Speedup report v2 §1.2, §4 P1, §5.3, §10.2, §11.2 Phase 1.

## What landed

- **`_daily_cache_row_from_prior`** extracted from
  `data/suppliers.py:build_daily_cache_from_lake` as a module-level helper.
  The legacy loop's per-symbol row math (ATR / EMA / 20d rolling means)
  collapses into one helper call; the helper is also consumed by the batch
  builder so both paths share identical arithmetic.
- **`data/daily_cache_batch.py`** (new) — `build_daily_cache_for_sessions_from_lake(...)`:
  reads each symbol's daily parquet ONCE over
  `[min(sessions) - lookback_days, max(sessions)]` (vs. once per
  `(symbol, session)` in the legacy path) and slices per session
  in memory. The returned `dict[date, DataFrame]` is bit-for-bit equal
  to the legacy per-session output (column list / row order / floats
  within `1e-12`).
  * Truncated-EMA semantics preserved — EMA computed INSIDE
    `_daily_cache_row_from_prior` on the per-session slice, NOT once
    over the full symbol history (the 400-day truncation IS the
    strategy). Pinned by
    `test_batch_daily_cache_truncated_ema_parity`.
  * Endpoint semantics mirror `MarketDataStore.daily_bars` (`[start, end]`
    inclusive) — no lookahead leaks via the inclusive read because the
    per-session slice still uses `prior["_sd"] < session`.
- **Wired behind `optuna.acceleration.batch_daily_cache.enabled`**
  (default `false`) in `optuna/fold_context.py:_build_one_fold_context`.
  Legacy mode runs the per-session loop unchanged; batch mode collects
  the per-session symbol map, then defers to the batch builder once
  after the loop. The fold-context build is timed into
  `fold_context_build_seconds` regardless of the flag.
- **`utils/profile_counters.py`** expanded with 7 Phase 1 fields
  (`daily_parquet_reads`, `daily_cache_symbols`, `daily_cache_sessions`,
  `daily_cache_batch_load_seconds`, `daily_cache_batch_slice_seconds`,
  `fold_context_build_seconds`, `worker_context_build_seconds`).
  Integer fields default 0, float-typed fields default 0.0; `inc(...)`
  handles both. All increments stay gated on
  `_COUNTERS_ENABLED` (default off).
- **`_PhaseProfile` + `_write_phase_profile_json`** in
  `optuna/walkforward_runner.py`. Each call to `run_walkforward_study(...)`
  binds a `ProfileCounters` context and times five phases
  (`resolve_config`, `preflight`, `fold_context_precompute`,
  `optuna_optimize`, `finalize`). The phase profile JSON is written at
  `paths.artifact_root/optuna/<study_name>__phase_profile.json` on
  every exit path:
  * preflight short-circuit (Phase 0),
  * structural-exception escape,
  * zero-valid-trials fail,
  * success path (also surfaced as `result["phase_profile_path"]`).
  Schema matches speedup report v2 §5.8 — `phase_seconds`,
  `counters`, `memory.rss_peak_gib`, `config_hash`, `dataset_hash`,
  `code_hash`.
- **`worker_context_build_seconds`** is also recorded by
  `make_walkforward_objective_for_worker(...)` so the phase-profile JSON
  can attribute the amortised worker rebuild cost in parallel runs.
- **`scripts/benchmark_daily_cache_phases.py`** (new) — operator-driven
  sweep that exercises `build_fold_contexts(...)` in `--mode legacy` vs
  `--mode batch` and writes a JSON with wall-clock, peak RSS, profile
  counters, and the per-mode parquet-read totals. Not asserted by any
  test.

## New tests

- `tests/unit/data/test_daily_cache_row_helper_extracted.py` (4):
  helper-row canonical keys, EMA lag-3 fallback path, ATR-shorter-than-window
  fallback, legacy builder calls the helper byte-for-byte.
- `tests/parity/test_batch_daily_cache_matches_legacy_exact.py` (2, parametrized):
  6-symbol mixed lake — split-like, missing-days, short-history,
  session_date-present, timestamp-only, present-dense — exact match for
  `lookback_days in (400, 30)`.
- `tests/parity/test_batch_daily_cache_preserves_row_order.py` (1):
  alphabetical row order is wrong; caller-provided order wins.
- `tests/parity/test_batch_daily_cache_no_lookahead.py` (1): mutating
  the lake with a post-`s0` extreme close must not change `out[s0]`.
- `tests/parity/test_batch_daily_cache_truncated_ema_parity.py` (1):
  legacy vs batch EMA agree within `1e-12`; both diverge from
  full-history EMA by > `1e-6` at the truncation boundary
  (`lookback_days=30`, span 10).
- `tests/parity/test_batch_daily_cache_handles_missing_symbol_partition.py`
  (1): a symbol with no parquet is silently dropped by both builders.
- `tests/integration/test_fold_context_batch_mode_matches_legacy.py` (1):
  `build_fold_contexts(...)` produces identical
  `daily_cache_by_session` in legacy vs batch modes via the config
  flag.
- `tests/integration/test_walkforward_batch_daily_cache_objective_parity.py`
  (2): `n_trials=2` walkforward parity (`best_value` within `1e-9`,
  `best_params` element-wise within `1e-9`); phase-profile JSON lands on
  disk on the success path and carries every required key.

## Default-off discipline

- `optuna.acceleration.batch_daily_cache.enabled` is `false` in every
  config under `configs/` (unchanged — the flag is additive). Operators
  flip it on AFTER benchmark evidence confirms wall-clock improvement
  on the workstation.
- `_COUNTERS_ENABLED` remains `False` by default; the timing fields
  cost zero outside `profile_counters_context(...)`. The
  `run_walkforward_study(...)` body now binds the context for its
  duration, so a study's counters are written into the phase-profile
  JSON without affecting other callers.

## Tests

| Gate | Result | Time |
|---|---|---|
| `make test-fast` (unit + parity) | **968 passed**, 0 failed | 39.1s |
| `make test-integration` (timeout=300) | **322 passed**, 2 skipped (PG-gated), 13 deselected (live + slow) | 13:30 |

## Branch

`feature/phase-1-batch-daily-cache` — merged to `dev` with `--no-ff`.
