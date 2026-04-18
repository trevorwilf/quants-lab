# Phase 11 Report — Sweep Notebook Factory

**Date**: 2026-04-17

## Files Created

- `create_sweep_nb_directional.py` — CLI tool generating runnable .ipynb for
  MR or EMA sweeps. Features:
  - HARD-STOP preflight: validate_candles(strict=True) for both intervals
    (signal and regime for EMA).
  - Soft warning for missing XMR-USDT per-pair override.
  - Optuna study creation + n_trials execution.
  - Canonicalize best trial, export YAML, validate round-trip.
  - Informational-only release gates printed regardless of pass/fail.

- `tests/unit/test_sweep_notebook_directional_generation.py` — 6 tests:
  notebook builds for both strategies, generated code `ast.parse()`s, MR does
  not inject `regime_candles`, EMA does.

All 6 tests pass.

## Phase 11 — Complete
