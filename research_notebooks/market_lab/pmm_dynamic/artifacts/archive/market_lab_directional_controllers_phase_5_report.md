# Phase 5 Report — Search Spaces

**Date**: 2026-04-17

## Files Created

- `pmm_lab/optuna/search_space_mean_reversion_bb_rsi.py`
  - Sampled: `bb_length`, `bb_std`, `bbp_entry_threshold`, `rsi_length`,
    `rsi_entry_threshold`, `use_trend_filter`, `trend_ema_length`,
    `atr_length`, `max_atr_pct_for_entry` (log, tightened to 0.005-0.10),
    `volume_filter_window`, `min_volume_quantile`, `cooldown_time`
    (lower bound = max(2×bar_interval, 300)), `stop_loss`, `take_profit`,
    `time_limit`, `take_profit_order_type`, `trailing_stop_activation`,
    `trailing_stop_delta`, `total_amount_quote`.
  - Fixed: `min_trend_slope=0.0` (D17), `max_trades_per_day=6` (D3),
    `max_spread_pct=0.006` (D2), `max_executors_per_side=1`.

- `pmm_lab/optuna/search_space_ema_regime_hold.py`
  - Sampled: `regime_ema_fast`, `regime_ema_slow` (enforced > fast),
    `regime_adx_length`, `regime_adx_threshold`, `volume_filter_window`,
    `min_volume_quantile`, `cooldown_time` (lower bound uses
    `signal_interval_seconds`), triple-barrier params,
    `total_amount_quote`.
  - Fixed: `hold_mode="reentry"` (D4), `max_executors_per_side=1`.

## Tests Added

- `tests/unit/test_search_space_mr_bb_rsi.py` — 10 tests.
- `tests/unit/test_search_space_ema_regime_hold.py` — 6 tests.

All 16 pass.

## Phase 5 — Complete
