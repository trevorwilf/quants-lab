# Per-trial speedup: startup_dq_cache fix (the dominant lever)

A real single-fold cProfile (`scripts/_profile_one_fold.py`, on the live
`_local_container_matrix.yml` path) overturned every prior hypothesis: the
post-matrix per-trial is **~81% `build_data_quality_report`**, rebuilt IN FULL on
every fold (~254 s of ~36k daily-parquet reads). The scan was ~18%, the exit
path <2%, and `_flag` (the deferred "optimization #2") ~1% — so #2 was correctly
dropped.

## Root cause — the cache never hit

`startup_dq_cache` (a prior Phase-3 optimization) builds the DQ report's
invariant half ONCE per fold context and is meant to reuse it per trial. It was
silently falling back to a full rebuild every fold because the cache `_cache_key`
mismatched on `symbols_hash`:

* stamp side (`fold_context`) hashed the per-fold **eligible-symbol union** (826);
* check side (`backtester`) hashed
  `{s["symbol"] for u in universe.values() for s in u.get("symbols", [])}` —
  **empty** on the raw `{symbol: record}` PIT universe (`.get("symbols")` absent
  there) → the empty-string hash, never matching (`scripts/_diag_dq_cache_key.py`
  confirmed: stamp n=826 vs check n=0).

## Fix (two parts)

1. **Key agreement** — new shape-robust helper
   `universe.builder.dq_cache_symbol_set(universe_by_session)` (eligible union for
   BOTH the raw `{symbol: record}` and scanner-snapshot `{"symbols": [...]}`
   shapes). Used on both sides: `fold_context` stamp + `backtester` check (via a
   new `cache_key_symbols` arg threaded from `run_backtest`). `requested_symbols`
   / the dataset lineage are left untouched — this only fixes the cache key.

2. **Skip the redundant reads** — keying agreement alone gave only 1.02×: the
   trial-dependent checks (`coverage_missing_exit_path`, `quote_coverage`,
   `replay_quote_age`) re-read the SAME daily bars, so caching the invariant
   *checks* doesn't avoid the *reads*. New `reuse_cached_invariant_only` arg to
   `_build_dq_report_with_optional_cache`: on a cache hit, return the cached
   invariant report and SKIP the trial-dependent rebuild entirely. `run_backtest`
   enables it only when `artifact_mode == "objective_minimal"` AND
   `sim_mode in {current_code_parity, smoke_fixture}` — modes that gate ONLY on
   the invariant adjustment checks (`evaluate_startup_dq`) and don't persist the
   report. `full` mode + `intended_realism` keep the complete report.

## Why it's objective-safe

For current_code_parity the DQ report does NOT change the trades: `evaluate_startup_dq`
gates only on the invariant adjustment checks (which the fix preserves), and the
objective is computed from trades. Proven, not assumed:

* **A/B (`scripts/_ab_dq_cache.py`, real fold)**: cache OFF (full rebuild) vs ON
  (hit + skip) → `full_builds=0 cached_hits=1`, **308.8 s → 54.2 s = 5.70×**,
  `FoldResult` diffs **NONE — byte-identical objective**.
* `tests/parity/test_dq_cache_key_symbols_parity.py` — helper + key-agreement
  regression lock (incl. the exact empty-on-raw bug).
* Integration green: `test_objective_minimal_parity`,
  `test_run_validation_folds_propagates_startup_dq`,
  `test_fold_context_parity` (full study WITH vs WITHOUT contexts → identical),
  `test_full_mode_gate_dump_unchanged`, `test_scan_matrix_{walkforward_fold,compatibility_objective}_parity`,
  the event-loop backtester tests. Host unit+parity: 1504 passed.

## Impact

Per-fold ~313 s → ~54 s; per-trial (3 folds) ~940 s → ~165 s. The invariant DQ
(~254 s × 3) is now paid ONCE per fold context at study startup, not per trial.
5000-trial projection drops from ~100–120 h to **~15–25 h** (inside the 24–48 h
goal). Combined with the byte-identical exit-path pass shipped earlier
(`per_trial_sim_exit_speedup.md`). Restart the study to pick it up.
