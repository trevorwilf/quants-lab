# Phase 2 Report — Feature Modules & TA Utils Shim

**Date**: 2026-04-17
**Objective**: Strategy-independent feature arrays matching the Hummingbot
controllers' math exactly.

## Files Created

- `pmm_lab/features/ta_utils_shim.py` — verbatim port of
  `hummingbot/strategy_v2/utils/ta_utils.py` (ema, rsi_wilder, true_range,
  atr_wilder, adx_wilder, bollinger_bands, bollinger_percent_b, donchian_high,
  rolling_volume_quantile_ok).
- `pmm_lab/features/mean_reversion_bb_rsi_features.py` — MRBBRSIFeatureConfig
  + compute_mr_bb_rsi_features. Vectorized default (D9), sliding-window via
  controller_compat=True for fixture generation.
- `pmm_lab/features/ema_regime_hold_features.py` — EMARegimeHoldFeatureConfig
  + compute_ema_regime_hold_features. Multi-timeframe merge via `pd.merge_asof(..., direction='backward')`.

## Tests Added

- `tests/unit/test_ta_utils_shim_parity.py` — 8 parity tests vs hummingbot (all pass with hummingbot on PYTHONPATH).
- `tests/unit/test_mr_bb_rsi_features.py` — 7 tests: contract, signal values, warmup, determinism, no-lookahead.
- `tests/unit/test_ema_regime_hold_features.py` — 5 tests: contract, multi-timeframe merge, determinism.
- `tests/unit/test_ema_regime_hold_timestamp_leakage.py` — dedicated leak test for vectorized path + replay path (marked slow).
- `tests/unit/test_mr_bb_rsi_controller_equivalence.py` — signal-array parity to controller-math replica.
- `tests/unit/test_ema_regime_hold_controller_equivalence.py` — analogous for EMA.

## Test Results

All Phase 2 tests pass:

- MR + EMA feature tests (13 tests): **pass**
- TA shim parity (8 tests): **pass** (with hummingbot on PYTHONPATH)
- Controller equivalence (2 tests): **pass** (with hummingbot on PYTHONPATH)

Without hummingbot on PYTHONPATH, the shim-parity and controller-equivalence
tests skip cleanly via `pytest.importorskip`.

## Notes

- `timestamp_mode='open'` shifts signals forward by 1 bar (D1). Signal at bar
  t now reflects indicators computed from close[0..t-1] — prevents the
  strategy from using a close value it cannot yet have observed.
- `controller_compat=True` is expensive (O(n × max_records)) on the EMA
  replay path. The replay test uses smaller inputs to stay under timeouts.
- `_compute_controller_compat` on MR is O(n × max_records × indicator_cost).
  We do not exercise MR replay parity tests at large n in this phase — the
  replay code path is retained for future fixture generation.
- Vectorized path matches controller math to `atol=1e-10` on the equivalence
  test (single controller_compat=False run).
- D18 (volume_filter_window warmup guard) is enforced at the canonicalizer
  layer, not here. The feature module honors whatever window the caller
  passes.

## Escalations

None.

## Phase 2 — Complete
