# `market_lab` Directional Controllers — Full PMM Parity FINAL

**Date**: 2026-04-17

## 1. Section status

| # | Section | Status |
|---|---|---|
| 0 | Baseline confirmation | **completed** |
| 1 | `to_fingerprint()` on MR/EMA configs | **completed** |
| 2 | Generalize signal cache | **completed** |
| 3 | Generalize validation helpers | **completed** |
| 4 | `TqdmProgressCallback` | **completed** |
| 5 | Rewrite cell 8 in 4 notebooks | **completed** |
| 6 | Upgrade Results Summary cell 10 | **completed** |
| 7 | Final verification + FINAL report | **completed** |

## 2. Before/after test counts

| Moment | Passed | Skipped | Failed | Duration |
|---|---|---|---|---|
| Baseline (pre-work) | 1252 | 58 | 0 | 44.74s |
| After full-parity work | **1355** | 59 | 0 | 45.99s |

Net delta: **+103 tests** (exceeds the "at least +20" target in Section 7A).

Section-level counts:
- Section 1: +6 tests (`test_config_fingerprint.py`, one skip in EMA covers — spec behavior)
- Section 2: +7 tests (`test_signal_cache_multi_strategy.py`)
- Section 3: +11 tests (`test_validation_helpers_multi_strategy.py`)
- Section 4: +3 tests (`test_tqdm_progress_callback.py`)
- Section 5: +67 tests (`test_direction_custom_cell8_completeness.py`)
- Section 6: +10 tests (`test_direction_custom_cell10_compact_table.py`)
- 1 existing test updated (MagicMock → real SimConfig) to track strict isinstance dispatch

## 3. Commands + output (Section 7A and 7B)

### 7A — Full test suite

```
$ pytest tests/ -q --ignore=tests/integration/test_mongo_live.py --ignore=tests/integration/test_optuna_smoke.py 2>&1 | tail -10
...
1355 passed, 59 skipped, 30 warnings in 45.99s
```

### 7B — Grep checks

```
$ === to_fingerprint on MR/EMA configs ===
pmm_lab/strategies/mean_reversion_bb_rsi.py
pmm_lab/strategies/ema_regime_hold.py

$ === signal_cache_key branches ===
9  (type-tag + 7 MR fields + 1 EMA mention; substring appears 9 times)

$ === TqdmProgressCallback exists ===
pmm_lab/optuna/callbacks.py:65:class TqdmProgressCallback:

$ === All 4 notebooks cell 8 are >=400 lines ===
  notebooks/direction-custom/mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb: 629 lines
  notebooks/direction-custom/mean_reversion_bb_rsi_retest_sweep.ipynb: 629 lines
  notebooks/direction-custom/ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb: 667 lines
  notebooks/direction-custom/ema_regime_hold_retest_sweep.ipynb: 667 lines
```

All checks pass.

## 4. Files modified

| File | Description |
|---|---|
| `pmm_lab/strategies/mean_reversion_bb_rsi.py` | Added `to_fingerprint()` method to `MeanReversionBBRSIStrategyConfig` |
| `pmm_lab/strategies/ema_regime_hold.py` | Added `to_fingerprint()` method to `EMARegimeHoldStrategyConfig` (with ndarray → bytes handling for `_regime_candles`) |
| `pmm_lab/objective/signal_cache.py` | Rewrote `signal_cache_key` + `SharedSignalCache.get_or_compute` to dispatch by config type (SimConfig/MR/EMA); added `regime_candles` kwarg |
| `pmm_lab/objective/holdout.py` | Generalized `evaluate_holdout` — type hints → `Any`; added `engine_config`, `regime_candles`, `stress_runner_fn` kwargs; routed signals through cache; sim through `run_simulation` |
| `pmm_lab/objective/recent_window.py` | Same generalization pattern as holdout |
| `pmm_lab/optuna/sensitivity.py` | Generalized `compute_sensitivity` — added `canonicalize_fn` and `regime_candles` kwargs; `_unpack()` handles SimConfig vs CandidateBundle returns; sim via `run_simulation` |
| `pmm_lab/objective/stress_selection.py` | Added `shared_signal_cache`, `dataset_key`, `regime_candles`, `apply_scenario_fn` kwargs; non-SimConfig skips scenarios without an apply_scenario_fn; robust_score falls back to baseline when no scenarios ran |
| `pmm_lab/optuna/callbacks.py` | Added `TqdmProgressCallback` with optional `show_best=True` postfix |
| `tests/unit/test_signal_cache_key_dataset_scope.py` | Updated `test_get_or_compute_caches_result` to use a real `SimConfig` (MagicMock no longer duck-types through strict `isinstance`) |
| `notebooks/direction-custom/mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb` | Cell 8 rewritten (135 → 629 lines); cell 10 upgraded to compact results table |
| `notebooks/direction-custom/mean_reversion_bb_rsi_retest_sweep.ipynb` | Same as above |
| `notebooks/direction-custom/ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb` | Cell 8 rewritten (145 → 667 lines, dual-stream); cell 10 upgraded |
| `notebooks/direction-custom/ema_regime_hold_retest_sweep.ipynb` | Same as above |

## 5. Files created

| File | Description |
|---|---|
| `pmm_lab/sim/runner_dispatch.py` | New — `run_simulation` + `run_simulation_cold` dispatch by config type (SimConfig/MR/EMA) |
| `tests/unit/test_config_fingerprint.py` | 6 tests covering MR + EMA `to_fingerprint()` |
| `tests/unit/test_signal_cache_multi_strategy.py` | 7 tests covering multi-strategy signal-cache dispatch |
| `tests/unit/test_validation_helpers_multi_strategy.py` | 11 tests — MR and EMA through holdout, recent_window, sensitivity, stress_selection, runner_dispatch |
| `tests/unit/test_tqdm_progress_callback.py` | 3 tests covering the new callback |
| `tests/unit/test_direction_custom_cell8_completeness.py` | 67 parametrized tests checking cell-8 line count, phase-name coverage, tqdm imports, `to_fingerprint` dedup, regime_candles presence (EMA), and AST parse of concatenated code cells |
| `tests/unit/test_direction_custom_cell10_compact_table.py` | 10 tests checking the new compact results table + retest notebooks' Cross-Pair Ranking retention |
| `notebooks/direction-custom/_build_cell8.py` | Cell-8 generator (idempotent; notebook remains source of truth) |
| `notebooks/direction-custom/_build_cell10.py` | Cell-10 generator (idempotent) |
| `artifacts/market_lab_directional_controllers_full_parity_baseline.md` | Pre-work baseline snapshot |
| `artifacts/full_parity_section_2_investigation.md` | Required by Section 2B |
| `artifacts/full_parity_section_3_investigation.md` | Required by Section 3C |
| `artifacts/pmm_cell8.py` | Reference — PMM's cell 8 extracted for comparison |
| `artifacts/mr_multi_cell8.py`, `ema_multi_cell8.py` | Pre-rewrite snapshots of the existing MR/EMA cell 8s |

## 6. Escalations

None. Every section completed per its acceptance criteria.

## 7. Output Sample

What a user should expect on stdout when running cell 8 of
`mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb`:

```
Pairs:   0%|          | 0/18 [00:00<?, ?it/s]

============================================================
  [1/18] mexc / APT-USDT / 5m
============================================================
  Split: dev=41280 holdout=10320 recent=8064
  Candles: 51,648  Days: 179.3  WF: 42.0/14.0/14.0d  Ref: 12.3050
trials:  45%|████▌     | 225/500 [00:32<00:40,  6.8trials/s, best=0.1234]

  Phase 1: 498 complete, 2 pruned, best=0.1471
  Phase 1 time: (12.4min)
  Phase 2: controller_compat=True (search=False)
  Deduped: 25 -> 18 unique configs
  Best: trial 217  robust=0.1105  PnL=4.21%  trades=23  (14.7min)
  Stress diag: evaluated=18 pruned=5 cache_hits=43 misses=18
  Recent 28d [BLOCKER]: PASS —
  Recent 14d [INFO]: PASS —
  Recent 7d [INFO]: PASS —
  Holdout: PASS
  Sensitivity: penalty=0.2083
  Clustering: CLUSTERED
  Parity: short=N/A
  Total time: (15.3min)  Gates: 8/12
  EXPORTED  yaml=artifacts/direction-custom/mr_bb_rsi/mexc/mexc_apt_usdt_5m_screening_best.yml
Pairs:   6%|▌         | 1/18 [15:23<4:21:31, 922s/it, mexc/APT-USDT]

============================================================
  [2/18] mexc / ATOM-USDT / 5m
============================================================
...
============================================================
SWEEP COMPLETE: 18 connector/pair combinations in 275.4 minutes
============================================================

SWEEP RESULTS SUMMARY
============================================================
Status counts: {'complete': 14, 'audit_fail': 2, 'no_completed_trials': 2}

Per-pair outcomes:
  [complete            ] mexc     APT-USDT        score=0.110  yaml=artifacts/direction-custom/...

====================================================================================================
COMPACT RESULTS TABLE (sorted by robust_score descending)
====================================================================================================
Rank  Connector   Pair                Robust   Holdout   Recent28d    Gates     Time  YAML
----------------------------------------------------------------------------------------------------
   1  mexc        APT-USDT            0.1105    0.0972      0.0844     8/12     179d  mexc_apt_usdt_5m_screening_best.yml
   2  mexc        ATOM-USDT           0.0988    0.0812      0.0701     7/12     176d  mexc_atom_usdt_5m_screening_best.yml
   3  mexc        NEAR-USDT           0.0874    0.0703      0.0598     7/12     180d  mexc_near_usdt_5m_screening_best.yml
...
====================================================================================================
```

Key user-facing improvements:
- Dual tqdm bars (outer "Pairs", inner "trials") with live best-score postfix
- Per-pair lifecycle log: split → candles+WF → Phase 1 → Phase 2 → Recent windows (28d/14d/7d) → Holdout → Sensitivity → Clustering → Parity → Gates/Time → Export
- Sorted compact table at the end (Rank/Connector/Pair/Robust/Holdout/Recent28d/Gates/Time/YAML)
- Every release gate is **informational** — only strict data audit short-circuits a pair

## Status: COMPLETE
