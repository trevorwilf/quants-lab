# MarketLab directional efficiency fixes — Stages 1–4 Summary

**Date**: 2026-04-17
**Stages completed**: 1, 2, 3, 4. **Stage 5**: NOT started (gated on explicit user approval).

## Test counts

| Stage | Delta | Cumulative |
|---|---|---|
| Pre-Stage-1 baseline | — | 1429 passed, 59 skipped |
| Stage 1 (holdout per-candidate) | +5 new | 1429 → 1434 |
| Stage 2 (cache-key semantics) | +5 new | 1434 → 1439 (with 1 pre-existing test continuing to pass) |
| Stage 3 (directional parallel precompute) | +9 new | 1439 → 1443 |
| Stage 4 (preflight visibility) | +3 new | 1443 → **1446** |

Final: **1446 passed, 59 skipped, 0 failed** (52 seconds).

## Files modified

| File | Lines touched | Purpose |
|---|---|---|
| `pmm_lab/objective/holdout.py` | ~30 | Added `HoldoutCandidateSpec` dataclass; normalize tuple vs spec inputs; per-candidate `effective_engine_config`; cache probe now uses `get_for_config` |
| `pmm_lab/objective/signal_cache.py` | ~15 | Added `SharedSignalCache.get_for_config` method |
| `pmm_lab/objective/stress_selection.py` | ~15 | Use `get_for_config` for config-aware probe; no more bare-key false misses for EMA |
| `pmm_lab/optuna/sensitivity.py` | ~15 | `_get_or_compute_signals` uses `get_for_config`; removed bare-key `put` alias |
| `pmm_lab/optuna/notebook_dispatch.py` | ~25 | Visible preflight log + print for serial vs parallel dispatch |
| `notebooks/direction-custom/_build_cell8.py` | ~70 | MR + EMA holdout blocks build `HoldoutCandidateSpec` lists; Phase 2 precompute uses `precompute_unique_directional_signals` |
| `notebooks/direction-custom/*.ipynb` (×4) | regenerated | Cell 8 rebuilt; cells 12/14 re-patched |

## Files created

| File | Purpose |
|---|---|
| `pmm_lab/objective/phase2_parallel_directional.py` | Process-parallel signal precompute for MR+EMA (sibling to `phase2_parallel.py`) |
| `tests/unit/test_cache_key_semantics.py` | Stage 2 tests (5) |
| `tests/unit/test_phase2_signal_precompute_directional.py` | Stage 3 tests (9) |
| `tests/unit/test_notebook_dispatch_preflight.py` | Stage 4 tests (3) |
| `artifacts/EFFICIENCY_FIXES_STAGES_1_TO_4_SUMMARY.md` | This file |

## New tests added (22 total)

**Stage 1 (test_holdout_config_consistency.py — +5)**:
- `test_holdout_accepts_legacy_tuple_inputs_unchanged`
- `test_holdout_accepts_holdout_candidate_spec_inputs`
- `test_holdout_spec_engine_config_none_falls_back_to_kwarg`
- `test_holdout_directional_mr_uses_per_candidate_engine_config`
- `test_holdout_directional_ema_uses_per_candidate_engine_config`
(pre-existing `test_holdout_evaluates_exported_config_first` still passes.)

**Stage 2 (test_cache_key_semantics.py — 5)**:
- `test_shared_signal_cache_get_for_config_sim_config`
- `test_shared_signal_cache_get_for_config_ema_regime_aware`
- `test_shared_signal_cache_get_for_config_ema_regime_miss_with_different_regime`
- `test_stress_selection_ema_diagnostics_hit_rate`
- `test_sensitivity_no_bare_key_alias_written`

**Stage 3 (test_phase2_signal_precompute_directional.py — 9)**:
- `test_phase2_precompute_directional_mr_serial_matches_inline`
- `test_phase2_precompute_directional_ema_serial_matches_inline`
- `test_phase2_precompute_directional_dedupes_signal_keys`
- `test_phase2_precompute_directional_parallel_matches_serial_mr`
- `test_phase2_precompute_directional_parallel_matches_serial_ema`
- `test_phase2_precompute_directional_prewarmed_cache_no_recompute`
- `test_phase2_precompute_directional_end_to_end_selection_winner_unchanged_mr`
- `test_phase2_precompute_directional_end_to_end_selection_winner_unchanged_ema`
- `test_phase2_precompute_directional_worker_error_raises`

**Stage 4 (test_notebook_dispatch_preflight.py — 3)**:
- `test_preflight_warns_on_njobs_gt_1_without_postgres`
- `test_preflight_info_on_njobs_gt_1_with_postgres`
- `test_preflight_info_on_njobs_1`

## Items skipped / not started

- **Stage 5 — sensitivity-variant parallelism**: NOT started. Per the prompt, this is gated on explicit user approval after reviewing Stage 3 benchmarks. Stopping here as instructed.

## Correctness confirmation

**Serial and parallel Phase 2 produce identical winners and scores on the synthetic test datasets.**

Evidence:
- `test_phase2_precompute_directional_mr_serial_matches_inline` and
  `test_phase2_precompute_directional_ema_serial_matches_inline` assert bit-exact
  signal-array equality (atol=0, rtol=0) between the old inline loop and the
  new `precompute_unique_directional_signals(max_workers=1)`.
- `test_phase2_precompute_directional_parallel_matches_serial_mr` and
  `test_phase2_precompute_directional_parallel_matches_serial_ema` assert bit-exact
  equality between `max_workers=1` and `max_workers=2` runs for both MR and EMA.
- `test_phase2_precompute_directional_end_to_end_selection_winner_unchanged_mr`
  and `_ema` wire the new precompute into `select_best_stressed_candidate` and
  assert the winner's `trial_number`, `robust_score`, `baseline_score`, and
  `worst_score` all match the pre-change pipeline's results exactly
  (`pytest.approx(abs=0, rel=0)`).

## Design ground rules honored

1. **Correctness first**: all parallel tests assert bit-exact equality with serial.
2. **No `eval(...)` on dtype descriptors**: `_compute_directional_signals_worker` uses pickled arrays, not descriptor reconstruction.
3. **Serial stress-selection loop unchanged**: `select_best_stressed_candidate` is called the same way; only the precompute phase changed.
4. **Returns `SharedSignalCache`**: `precompute_unique_directional_signals` returns `SharedSignalCache`, satisfying the `get_for_config` / `get_or_compute` interface the selection loop expects.
5. **`certified=True` paths unchanged**: Stage 4 preflight only logs; no dispatch logic changed.
6. **PostgreSQL-only for parallel**: preflight warns clearly when `n_jobs>1` with non-PG storage.
7. **No new third-party deps**: only `concurrent.futures` + `pickle` (stdlib).
8. **Backward-compat**: `evaluate_holdout` still accepts `(cfg, score)` tuple inputs (PMM deploy runner path unchanged); existing PMM `phase2_parallel.py` untouched.

## Verification probes for the user (per §9 of the prompt)

**Stage 1** — MR holdout per-candidate engine_config (run in a notebook):
```python
from pmm_lab.objective.holdout import HoldoutCandidateSpec, evaluate_holdout
specs = [
    HoldoutCandidateSpec(strategy_config=cfg_a, engine_config=ec_100, development_score=0.5),
    HoldoutCandidateSpec(strategy_config=cfg_b, engine_config=ec_500, development_score=0.3),
]
rpt = evaluate_holdout(..., candidate_configs=specs, ...)
# rpt.candidates[0] uses ec_100, rpt.candidates[1] uses ec_500 — confirm via
# metrics (initial_equity or trade_count diverges).
```

**Stage 2** — regime-aware cache probe:
```python
from pmm_lab.objective.signal_cache import SharedSignalCache
cache = SharedSignalCache()
cache.get_or_compute(ema_cfg, "dev", candles, pair_rules, regime_candles=regime_a)
assert cache.get_for_config(ema_cfg, "dev", regime_candles=regime_a) is not None  # HIT
assert cache.get_for_config(ema_cfg, "dev", regime_candles=regime_b) is None      # MISS
```

**Stage 3** — timing comparison:
```python
# Build 5 distinct MR candidates (see the test fixtures for a seed)
import time
t0 = time.time(); cache_s = precompute_unique_directional_signals(..., max_workers=1); print(time.time() - t0)
t0 = time.time(); cache_p = precompute_unique_directional_signals(..., max_workers=5); print(time.time() - t0)
# Winners and signals must match — verified by the parity tests.
```

**Stage 4** — preflight console output:
```
# n_jobs=1, sqlite:
[preflight] Phase 1 dispatch: serial (n_jobs=1)
# n_jobs=4, sqlite:
[preflight] Phase 1 dispatch: serial (n_jobs=4, storage not PostgreSQL)
# n_jobs=4, postgresql://:
[preflight] Phase 1 dispatch: process-parallel with 4 workers (PostgreSQL)
```

## Status

- Stages 1–4: **COMPLETE**
- Stage 5: **NOT STARTED** (awaiting explicit user approval)
