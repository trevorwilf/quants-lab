# Final summary — Bowaka v2 Optuna speedup v2 (Phases 0–6)

Speedup report v2 (`bowaka_v2_lab_optuna_speedup_v2_claude_code_prompt.md`).
All six phases landed on `dev` with `--no-ff` merges; the cardinal rule —
"a faster invalid optimization is worse than a slow valid optimization"
— is honoured: Phase 0 correctness ships on-by-default, every later
phase ships behind a default-off config flag with parity tests pinning
the legacy-vs-new bit-equality (or near-equality at the declared float
tolerance).

## Per-phase acceptance status

| # | Phase | Branch / merge | Result |
|---|---|---|---|
| 0 | P0 correctness — startup-DQ + incumbent enqueue | `feature/phase-0-optuna-correctness` → `9be2f98` | **green** |
| 1 | Exact batch daily-feature cache | `feature/phase-1-batch-daily-cache` → `d3d248c` | **green** |
| 2 | Parallel preflight + workstation overlays | `feature/phase-2-parallel-preflight-and-profile` → `f0b6bba` | **green** |
| 3 | Invariant startup DQ cache | `feature/phase-3-startup-dq-cache` → `1e497e2` | **green** |
| 4 | Session minute-window cache | `feature/phase-4-session-minute-window-cache` → `2bcd487` | **green** |
| 5 | Staged finalist testing pipeline | `feature/phase-5-staged-finalist-testing` → `e593a42` | **green** |
| 6 | Scan-matrix runtime (research-only) | `feature/phase-6-scan-matrix-runtime` → `46ecaac` | **green (scaffolding)** |

`dev` head: `46ecaac93d9228787118a4a64bd14bde753825a6`. `main` deliberately
not touched.

## Final test gate

`make test-all` on `dev` (post-Phase-6): **1396 passed, 2 skipped
(PG-gated), 15 deselected (live + slow), 0 failed** in 14:38.

| Suite | Count |
|---|---|
| `tests/unit` + `tests/parity` | 1048 passed |
| `tests/integration` | 348 passed |
| Skipped | 2 (PostgreSQL-gated parallel smoke / parity tests) |
| Deselected | 15 (live + slow markers) |

## New config flags added (default → operator action)

| Flag | Default | Phase | Where to flip |
|---|---|---|---|
| `optuna.acceleration.batch_daily_cache.enabled` | `false` | 1 | After workstation benchmark proves wall-clock win |
| `optuna.parallel.strict_parallel` | `false` | 2 | `.workstation.yml` sets `true` |
| `optuna.parallel.memory_reserve_gib` | `32` | 2 | `.workstation.yml` sets `62` |
| `optuna.acceleration.startup_dq_cache.enabled` | `false` | 3 | After benchmark proves wall-clock win (no objective drift by construction) |
| `optuna.acceleration.session_minute_window_cache.enabled` | `false` | 4 | Benchmark-only — dual-gated with `cached_suppliers` |
| `finalist_evaluation.*` (top_k, include_incumbent, stress_scenarios, ...) | included in the 3 generated optuna configs; pipeline is opt-in via the CLI | 5 | Operator runs `bowaka-v2-lab evaluate-finalists --study-dir ... --config ... --output ...` |
| `optuna.acceleration.scan_matrix.runtime_mode` | `disabled` | 6 | Scaffolding-only — refused at backtester opt-in until the parity bridge ships |

## Adoption checklist (speedup report v2 §12 mirror)

- [x] Current invalid raw-IEX adjusted-required config fails closed
      BEFORE trials (Phase 0). Pinned by
      `tests/integration/test_walkforward_fails_before_context_build_on_raw_lake.py`.
- [x] Incumbent trial no longer changes Optuna distributions (Phase 0).
      Pinned by
      `tests/unit/optuna/test_incumbent_enqueue_stable_search_space.py`.
- [x] Legacy and new daily cache match on fixtures (Phase 1).
      Six parity tests under `tests/parity/test_batch_daily_cache_*`
      plus one integration walkforward-objective parity test.
- [x] No final-holdout data is read during tuning. `HoldoutGuard.
      declare_finalist_read()` is the one authorised reader; the
      finalist-evaluation pipeline is the one authorised caller.
      Pinned by
      `tests/unit/optuna/test_holdout_guard_finalist_read_gate.py`.
- [x] Phase profile JSON is written for every study (Phase 1 task 5).
      Schema `phase_seconds` / `counters` / `memory.rss_peak_gib` /
      `config_hash` / `dataset_hash` / `code_hash`. Lands at
      `artifacts/optuna/<study_name>__phase_profile.json` on every
      exit path (preflight fail, structural escape,
      zero-valid-trials, success).
- [x] Valid trial count excludes sentinel and DQ-degraded failures
      (Phase 0 pre-existing + preserved through all phases).
- [x] Parallel strict mode fails early if storage/memory is not
      viable (Phase 2). `preflight_parallel_dispatch` runs BEFORE
      `build_fold_contexts`; strict-parallel skips parent context
      build entirely.
- [x] Finalist rerun includes incumbent and final holdout (Phase 5).
      `FinalistEvaluationConfig` with `include_incumbent=True` and
      `score_final_holdout=True` defaults.
- [x] Promotion artifact includes data/config/code hashes (Phase 5).
      `run_promotion_candidate` writes
      `promotion_artifact.json` with sort_keys=True for byte-equal
      repeats modulo `captured_at_utc` + `platform.node`.
- [x] Scan-matrix runtime defaults to `disabled` (Phase 6).
      `tests/integration/test_scan_matrix_runtime_mode_disabled_is_default.py`
      sweeps every `configs/bowaka_v2_*.yml` and pins the default.

## Deferred items (documented in per-phase artifacts)

- **Phase 5** — live-lake integration tests for the finalist pipeline
  (top_k_includes_incumbent / holdout_read_only_after_tuning /
  stress_scenarios_are_fold_local). Injectable-scoring API is in
  place so they can land without further refactor.
- **Phase 6** — compatibility-mode parity bridge
  (`MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat`) and the
  vectorized gate evaluator (`evaluate_one_scan_vectorized`). The
  scaffolding refuses at the backtester opt-in boundary; the parity
  matrix tests (`test_scan_matrix_feature_row_parity` /
  `_full_session_candidate_parity` /
  `_full_fold_backtest_parity`) need the bridge implemented first.

## Artifacts on disk

* `artifacts/phase-{0..6}-speedup-v2-summary.md` — per-phase summaries.
* `artifacts/final-summary-speedup-v2.md` — this file.
* `scripts/benchmark_daily_cache_phases.py` (Phase 1).
* `scripts/benchmark_optuna_workers.py` (Phase 2).
* `scripts/benchmark_session_minute_window_cache.py` (Phase 4).
* Runtime: `artifacts/optuna/<study_name>__phase_profile.json` per run.
* Benchmarks: `artifacts/benchmarks/*` per operator sweep.

## Operator next steps

1. Flip `optuna.acceleration.batch_daily_cache.enabled = true` after
   running `scripts/benchmark_daily_cache_phases.py --mode batch` and
   confirming the legacy parity tests still pass.
2. Switch to the workstation overlay
   (`configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml`)
   for production studies on the 192 GiB / 18-core box. Use the 10w
   / 12w / 16w overlays only for explicit benchmark sweeps.
3. After Stage A finishes, run `bowaka-v2-lab evaluate-finalists` on
   the study directory + the finalist-evaluation config block for
   Stage B; manually invoke `run_promotion_candidate` from the
   Python API for the chosen Stage C candidate.
4. Inspect `artifacts/optuna/<study>__phase_profile.json` to verify
   the wall-clock improvements the Phase 1 / 3 / 4 caches deliver
   before promoting them on the actual-IEX configs.

`main` deliberately not touched — that's the operator's call.
