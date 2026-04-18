# Phase 6 Report — Canonicalizers

**Date**: 2026-04-17

## Files Created

- `pmm_lab/optuna/canonicalizer_mean_reversion_bb_rsi.py`
- `pmm_lab/optuna/canonicalizer_ema_regime_hold.py`

Both canonicalizers:
- Set `executor_refresh_time = bar_interval_seconds` (D7).
- Set `latency_bars = 1` (D6).
- Apply trailing-stop soft constraints (zero activation → zero delta;
  delta >= activation → clamp to half).
- Check min notional at reference price; reject with detailed string.

MR-specific:
- D17: clamp `min_trend_slope` to 0.0, log warning if non-zero.
- D18: reject when `volume_filter_window + 50 > max(bb_length, trend_ema_length,
  rsi_length, atr_length) + 500`.

EMA-specific:
- D4: reject `hold_mode='hold'`.
- Require `regime_candles` and attach via `dataclasses.replace` to the
  strategy config's private `_regime_candles` field.
- D19: reject when slow-buffer or fast-buffer margins exceeded.

## Tests Added

- `tests/unit/test_canonicalizer_mr_bb_rsi.py` — 12 tests.
- `tests/unit/test_canonicalizer_ema_regime_hold.py` — 10 tests.

All 22 pass.

## Phase 6 — Complete
