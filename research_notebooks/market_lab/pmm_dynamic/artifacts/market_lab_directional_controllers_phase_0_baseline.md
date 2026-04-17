# Phase 0 Baseline Report — market_lab Directional Controllers

**Date**: 2026-04-17
**Objective**: Establish pre-change baseline for the 13-phase implementation.

## Git Heads

- **quants-lab HEAD**: `e1ae2894cc72182a3e833bc9de4333691c29bafe` (branch: `main`)
- **hummingbot HEAD**: `4aaecb0b0b9a38b72f0f819ade0d59625dc4aa71` (branch: `nonkyc`)

## Required File Presence

All verified present:

- `hummingbot/controllers/directional_trading/mean_reversion_bb_rsi_v1.py` — **present**
- `hummingbot/controllers/directional_trading/ema_regime_hold_v1.py` — **present**
- `hummingbot/hummingbot/strategy_v2/utils/ta_utils.py` — **present**
- `pmm_lab/strategies/macd_bb.py` — **present**
- `pmm_lab/optuna/canonicalizer_macd_bb.py` — **present**
- `configs/exchange_rules.yaml` — **present**

Note: Hummingbot controllers live under top-level `hummingbot/controllers/`, NOT under `hummingbot/hummingbot/controllers/`. The prompt's path spec was imprecise here; actual paths verified.

Runtime YAMLs found at `hummingbot/conf/controllers/nonkyc_xmr_usdt_{mean_reversion_bb_rsi_v1,ema_regime_hold_v1}.yml`.

## Baseline Test Suite Result

Command:
```
pytest tests/ -q --ignore=tests/integration/test_mongo_live.py --ignore=tests/integration/test_optuna_smoke.py
```

Result: **1068 passed, 54 skipped, 1 failed, 4 warnings** in 102.60s.

### Pre-existing failure (not caused by our work)

- `tests/unit/test_pipeline_runner.py::TestRunFullPipelineMini::test_run_full_pipeline_mini`
  - `KeyError: 'total_amount_quote'` in `pmm_lab/optuna/canonicalizer.py:97`
  - Appears to be a test that no longer matches the current canonicalizer signature/contract.
  - Our implementation is additive and must not increase this failure count.

**Bar for subsequent phases**: 1068 passing, 1 pre-existing failure, 54 skipped. No previously-passing test may regress.

## Artifacts Directory

`pmm_dynamic/artifacts/` already exists with `screener/` and `sweep/` subdirectories. New phase reports will live in this directory at the top level (not inside any subdirectory).

No `.gitignore` exists at `pmm_dynamic/` level. Repo-root `.gitignore` at `quants-lab/.gitignore` exists but does not exclude `artifacts/`. Not adding a local gitignore — phase reports are intentionally inspectable.

## Phase 0 — Complete

Ready to proceed to Phase 1 (three surgical edits: `defaults.py`, `exchange_rules.yaml`, `factory.py`).
