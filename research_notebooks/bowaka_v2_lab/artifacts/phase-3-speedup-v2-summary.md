# Phase 3 — Invariant startup DQ cache

Speedup report v2 §4 P4, §5.6, §10.x, §11.2 Phase 3.

## What landed

- **`_DQ_CHECK_INVARIANCE` classification dict + `DQ_CHECK_INVARIANCE_VERSION = 1`**
  in `data/data_quality.py`. Every check name `build_data_quality_report`
  emits is classified as `invariant` (depends only on lake/lineage/symbols/
  sessions/sim_mode/market_data flags/daily_cache) or `trial_dependent`
  (consumes a search-space leaf). The dict is the single source of truth
  for cache-vs-rebuild decisions; the conservative `dq_check_invariance(...)`
  helper defaults unknown names to `trial_dependent` so a forgotten
  classification never silently reuses a stale row.
  * Trial-dependent: `quote_coverage`, `coverage_missing_exit_path`,
    `replay_quote_age_violation` (consume `execution.max_quote_age_seconds`
    / `exits.max_hold_days` which ARE in the search space).
  * Everything else (audit / coverage_missing / adjustment / split / SIP /
    multi-level ingestion / session / feature / quote-status / replay
    error catchers) is invariant.
- **`classify_filter` kwarg** on `build_data_quality_report(...)` — when
  set to `"invariant"` or `"trial_dependent"` emits only the matching
  subset; default `None` preserves the legacy full report.
- **`merge_dq_reports(a, b)`** helper that concatenates check lists,
  dedupes by name (trial-dependent wins on collision), and recomputes
  `failed` / `passed` / `warned` / `required_failures` /
  `adjustment_gating_failures` from the merged checks.
- **`FoldRuntimeContext`** gains `startup_dq_report: Optional[dict] = None`
  and `startup_dq_failure: Optional[str] = None`. When the new
  `optuna.acceleration.startup_dq_cache.enabled` flag is on,
  `_build_one_fold_context` builds the invariant subset once per fold
  and stamps a `_cache_key` (lake_root, feed, symbols_hash, sessions,
  simulation_mode, gating market_data flags, DQ_CHECK_INVARIANCE_VERSION).
  Build failures degrade silently to `None` so the per-trial path
  rebuilds (best-effort cache, never the source of a study abort).
- **`run_backtest(...)` accepts `startup_dq_report=...`** — module-level
  dispatch via `sys.modules[__name__].build_data_quality_report` so
  `patch.object(backtester, "build_data_quality_report", ...)` reaches
  both the full-rebuild and trial-dependent paths (test ergonomic).
  Cache-key mismatch on any field → `log.warning(...)` + full rebuild
  (safer than reusing a possibly-stale row).
- **Plumbed through `_run_fold_backtest` + `_run_fold_backtest_objective`**
  — both pass `startup_dq_report=ctx.startup_dq_report` when a fold
  context is supplied (default `None` from a legacy callsite preserves
  the legacy build).
- **`ProfileCounters.startup_dq_builds` + `startup_dq_cached_hits`** —
  cumulative `int` counters; gated on the existing
  `_COUNTERS_ENABLED` flag.

## New tests

- `tests/unit/data/test_dq_check_invariance_classification.py` (5):
  version is positive int, every value is `invariant` or
  `trial_dependent`, unknown name → trial_dependent, expected
  trial-dependent set includes `quote_coverage` /
  `coverage_missing_exit_path` / `replay_quote_age_violation`, audit
  + coverage_missing + adjustment checks are invariant.
- `tests/unit/data/test_merge_dq_reports.py` (4): unique concatenation,
  empty-`b` case, collision picks `b`, `required_failures` rebuilt
  from merged checks.
- `tests/unit/sim/test_run_backtest_accepts_precomputed_dq_report.py`
  (1): a matching cache key skips the invariant rebuild — only one
  `build_data_quality_report` call (the trial-dependent half).
- `tests/unit/data/test_dq_cache_invalidation.py` (3): mismatched
  lake root, market_data flag, DQ_CHECK_INVARIANCE_VERSION each force
  a full rebuild AND emit a `startup_dq_cache miss` warning.
- `tests/integration/test_cached_startup_dq_matches_uncached_report.py`
  (1): cached fold context carries only invariant-classified checks;
  legacy fold context carries no cache.
- `tests/integration/test_cached_startup_dq_does_not_change_objective.py`
  (1, `@pytest.mark.slow`): walkforward `n_trials=2` parity — best_value
  within 1e-9 / best_params element-wise within 1e-9.

## Tests

| Gate | Result | Time |
|---|---|---|
| `make test-fast` | **1005 passed**, 0 failed | 45.7s |
| `make test-integration` (timeout=300) | **334 passed**, 2 skipped (PG-gated), 14 deselected (live + slow) | 13:53 |

## Default-off discipline

- `optuna.acceleration.startup_dq_cache.enabled` is `false` everywhere
  (additive flag). Flipping it on AFTER benchmark evidence stays an
  operator decision.
- The cache is best-effort — any build failure in `_build_one_fold_context`
  degrades to a `None` report and the per-trial path rebuilds. A trial
  never aborts because the cache failed.
- Cache invalidation is conservative — any mismatch in
  `_cache_key.lake_root` / `feed` / `symbols_hash` / `sessions` /
  `simulation_mode` / `market_data_keys` / `dq_check_invariance_version`
  rebuilds the full report with a logged warning.

## Branch

`feature/phase-3-startup-dq-cache` — merged to `dev` with `--no-ff`.
