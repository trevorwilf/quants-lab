# Phase 9 Report — Walk-Forward + Holdout Verification

**Date**: 2026-04-17

## Files Created

- `tests/unit/test_mr_bb_rsi_walkforward.py` — 2 tests (multiple folds,
  determinism).
- `tests/unit/test_ema_regime_hold_walkforward.py` — 1 test (multiple folds).
- `tests/unit/test_mr_bb_rsi_holdout.py` — 1 test (dev/holdout split + run).
- `tests/unit/test_ema_regime_hold_holdout.py` — 1 test.

All 5 pass.

## Note on holdout

`pmm_lab/objective/holdout.py::split_holdout` is strategy-generic and reusable;
`evaluate_holdout` is PMM-specific (it builds `SimConfig` objects). The holdout
tests therefore run the engine directly rather than use the PMM-specific
helper. Not creating a new `holdout_mr_bb_rsi.py` module — the existing
`split_holdout` is sufficient for informational holdout evaluation; the full
sweep notebook can reuse the strategy-agnostic `run_with_signals` against the
holdout slice.

## Phase 9 — Complete
