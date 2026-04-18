# Phase 7 Report — Objective Wrapper Dispatch

**Date**: 2026-04-17

## Files Modified (additive)

- `pmm_lab/optuna/objective_wrapper.py` — added two `if strategy_name == ...`
  branches at the top of the dispatch, above the existing MACD-BB branch.
  Also added `regime_candles: Optional[np.ndarray] = None` kwarg to
  `create_objective`. Existing PMM Dynamic and MACD-BB paths untouched.

## Files Created

- `pmm_lab/optuna/objective_wrapper_mr_bb_rsi.py` — `_create_mr_bb_rsi_objective`.
  Each fold constructs a fresh MR strategy instance (rolling 24h cap state
  must not leak across folds). Sets the `max_trades_per_day_binding_fraction`
  user_attr for diagnostics.
- `pmm_lab/optuna/objective_wrapper_ema_regime_hold.py` —
  `_create_ema_regime_hold_objective`. Raises `ValueError` at creation time if
  `regime_candles` is None.

## Tests Added

- `tests/unit/test_objective_wrapper_mr_bb_rsi.py` — 1 test (5000-bar synthetic, 1 trial).
- `tests/unit/test_objective_wrapper_ema_regime_hold.py` — 2 tests (missing-regime
  ValueError + 1-trial smoke).
- `tests/unit/test_objective_wrapper_dispatch_regression.py` — 2 tests verifying
  `macd_bb` and `pmm_dynamic` dispatch still returns callables.

All 5 tests pass.

## Phase 7 — Complete
