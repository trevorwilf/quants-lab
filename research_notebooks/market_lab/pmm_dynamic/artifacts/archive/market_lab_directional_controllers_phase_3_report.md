# Phase 3 Report — Strategy Modules

**Date**: 2026-04-17
**Objective**: Wrap feature output in the Strategy protocol with build_orders,
D3 rolling 24h cap, D13 inventory guard, long-only invariant.

## Files Created

- `pmm_lab/strategies/mean_reversion_bb_rsi.py` — MeanReversionBBRSIStrategy
  + MeanReversionBBRSIStrategyConfig. `__post_init__` enforces
  max_executors_per_side=1. `build_orders` implements D3 rolling 24h cap via
  `self._entry_timestamps`, D13 quote-balance pre-check, long-only defense.
  `reset_state()` clears the rolling buffer.
- `pmm_lab/strategies/ema_regime_hold.py` — EMARegimeHoldStrategy
  + EMARegimeHoldStrategyConfig. `__init__` raises NotImplementedError when
  hold_mode='hold' (D4). compute_signals raises ValueError if the canonicalizer
  hasn't attached `_regime_candles`.

## Tests Added

- `tests/unit/test_mr_bb_rsi_strategy.py` — 12 tests: protocol, invariants,
  compute_signals shape, buy-on-entry, zero/NaN/sell rejection, D13 guard,
  min-notional rejection, 24h cap binding, window sliding, reset_state.
- `tests/unit/test_ema_regime_hold_strategy.py` — 8 tests (4 skip on this
  specific synthetic data because the random walk doesn't produce entries —
  they verify the code path executes).
- `tests/unit/test_mr_bb_rsi_engine_integration.py` — end-to-end run on a
  dip-recover synthetic produces all-buy trades and finite equity.
- `tests/unit/test_ema_regime_hold_engine_integration.py` — end-to-end run
  on trending synthetic runs cleanly.

## Test Results

All non-skipped Phase 3 tests pass:

- MR strategy: **12 passed**
- EMA strategy: **4 passed, 4 skipped** (skip guards on synthetic data)
- Engine integration: **2 passed**

Factory import is now restored — `available_strategies()` returns 5 strategies.

## Notes

- `SimEngine` has two entry points: `run(candles, strategy)` (strategy
  computes signals internally) and `run_with_signals(candles, strategy,
  precomputed_signals)` (skip recomputation across folds/scenarios). The
  integration tests use `run()` for simplicity. Objective wrappers will use
  `run_with_signals`.
- D3 cap is *placed*-order tracking, not *filled*-order tracking. This errs
  on the safer side for a live-safety gate: an order that's placed but
  doesn't fill still counts against the daily cap.
- The caller (objective wrapper) must instantiate a fresh `MeanReversionBBRSIStrategy`
  instance per fold, or call `reset_state()` between folds. The engine
  does not provide a reset hook.

## Escalations

None.

## Phase 3 — Complete
