# Full Parity — Section 2 Investigation

**Date**: 2026-04-17

## Findings

### Q1. Does `CandleSimRunner` currently accept MR/EMA configs, or only `SimConfig`?

**Only SimConfig.** `CandleSimRunner.__init__` hardcodes `PMMDynamicStrategy.from_sim_config(config)` (line 64 of `pmm_lab/sim/runner.py`). It reads PMM-Dynamic-specific fields via `_sim_config_to_engine_config`.

**Consequence**: `SharedSignalCache.get_or_compute` currently cannot run with MR/EMA. It needs a dispatch branch that instantiates the right strategy.

### Q2. Is there already a factory-dispatch function that maps (strategy_config, pair_rules) → a runnable simulator?

**Yes — a *strategy* factory exists at `pmm_lab/strategies/factory.py`, but no *runner* factory.**

`create_strategy(name, config)` maps `str -> Strategy`, but the caller still has to wire `SimEngine(EngineConfig(), pair_rules)` separately. For signal-cache purposes, we don't need a full runner — we only need `strategy.compute_signals(candles)`.

**Consequence**: For the signal cache, dispatch by config type (not by name) and call the strategy's `compute_signals` directly. This avoids building an engine we don't need.

### Q3. What MR fields affect signal computation?

Every field of `MRBBRSIFeatureConfig` (verified against `pmm_lab/features/mean_reversion_bb_rsi_features.py`):

```
bb_length, bb_std, bbp_entry_threshold,
rsi_length, rsi_entry_threshold,
use_trend_filter, trend_ema_length, min_trend_slope,
atr_length, max_atr_pct_for_entry,
volume_filter_window, min_volume_quantile,
timestamp_mode, controller_compat
```

Execution-only fields (NOT signal-affecting, excluded from cache key):
- `max_spread_pct`, `max_trades_per_day`, `max_executors_per_side`

### Q4. What EMA fields affect signal computation?

Every field of `EMARegimeHoldFeatureConfig`:

```
regime_ema_fast, regime_ema_slow,
regime_adx_length, regime_adx_threshold,
volume_filter_window, min_volume_quantile,
hold_mode, timestamp_mode, controller_compat
```

EMA takes TWO candle streams. The cache key must only include config params; the `dataset_key` must distinguish datasets (e.g., `"dev"`, `"dev+regime"`). The `get_or_compute` signature needs a `regime_candles=None` kwarg that is required for EMA.

Note: `hold_mode` doesn't affect feature *values* per se, but it's in the feature config and the strategy rejects `'hold'` at init, so including it is safe and future-proof.

## Plan for 2C and 2D

### 2C — `signal_cache_key`

Add two isinstance branches before falling through to TypeError. Keep PMM branch unchanged. Type-tag string as first tuple element prevents cross-strategy collisions.

### 2D — `SharedSignalCache.get_or_compute`

Replace `CandleSimRunner(config, pair_rules).compute_signals(candles)` with:

- If SimConfig → `CandleSimRunner(cfg, pair_rules).compute_signals(candles)` (existing path).
- If MR → `compute_mr_bb_rsi_features(candles, feature_cfg)` where `feature_cfg` is built verbatim from the objective wrapper's construction (see `MeanReversionBBRSIStrategy.compute_signals` for the exact field mapping).
- If EMA → `compute_ema_regime_hold_features(candles, regime_candles, feature_cfg)` requires the kwarg; raise `ValueError` if missing.

`pair_rules` is unused on the MR/EMA paths since feature computation doesn't consult exchange rules. We keep it in the signature for backward compatibility.
