# market_lab Directional Controllers — Final Report

**Date**: 2026-04-17
**Scope**: Extend `pmm_lab` to backtest / Optuna-optimize / stress-test /
walk-forward / export two Hummingbot V2 directional controllers
(`mean_reversion_bb_rsi_v1` and `ema_regime_hold_v1`) for NonKYC XMR-USDT.

## Pre-existing Files Modified (exactly 4, all additive)

| File | Change |
|---|---|
| `pmm_lab/config/defaults.py` | +1 line: `"12h": 43200,` in `INTERVAL_SECONDS` (1A). |
| `configs/exchange_rules.yaml` | +2 blocks: `XMR-USDT` entry in both `mexc.pairs` and `nonkyc.pairs`, price_tick=0.01, amount_step=0.001, min_notional_quote=1.0 (1B). |
| `pmm_lab/strategies/factory.py` | +2 imports, +2 register calls for `mean_reversion_bb_rsi` and `ema_regime_hold` (1C). |
| `pmm_lab/optuna/objective_wrapper.py` | +2 dispatch branches at the top of `create_objective` (above MACD-BB); +1 `regime_candles` kwarg (7A). Existing PMM Dynamic / MACD-BB paths untouched. |

## New Modules by Category

### Features (Phase 2)
- `pmm_lab/features/ta_utils_shim.py` — verbatim port of HB ta_utils.
- `pmm_lab/features/mean_reversion_bb_rsi_features.py`
- `pmm_lab/features/ema_regime_hold_features.py` (multi-timeframe)

### Strategies (Phase 3)
- `pmm_lab/strategies/mean_reversion_bb_rsi.py` — includes D3 rolling 24h
  cap, D13 inventory guard, long-only invariant, `reset_state()`.
- `pmm_lab/strategies/ema_regime_hold.py` — D4 hold_mode guard, unwired
  regime candles raise ValueError.

### Search Spaces (Phase 5)
- `pmm_lab/optuna/search_space_mean_reversion_bb_rsi.py`
- `pmm_lab/optuna/search_space_ema_regime_hold.py`

### Canonicalizers (Phase 6)
- `pmm_lab/optuna/canonicalizer_mean_reversion_bb_rsi.py` — D17/D18 guards.
- `pmm_lab/optuna/canonicalizer_ema_regime_hold.py` — D4/D19 guards; wires
  `_regime_candles` via `dataclasses.replace`.

### Objective Wrappers (Phase 7)
- `pmm_lab/optuna/objective_wrapper_mr_bb_rsi.py`
- `pmm_lab/optuna/objective_wrapper_ema_regime_hold.py`

### Stress Modules (Phase 8)
- `pmm_lab/objective/stress_mean_reversion_bb_rsi.py`
- `pmm_lab/objective/stress_ema_regime_hold.py`

### YAML Export (Phase 10)
- `pmm_lab/export/hb_yaml_mr_bb_rsi.py` — `export_mr_bb_rsi_yaml`,
  `validate_export_mr_bb_rsi`.
- `pmm_lab/export/hb_yaml_ema_regime_hold.py` — `export_ema_regime_hold_yaml`,
  `validate_export_ema_regime_hold`.

### Sweep Notebook Factory (Phase 11)
- `create_sweep_nb_directional.py` — CLI tool.

## Test Counts

| Phase | Passed | Suite-level notes |
|---|---|---|
| Baseline (Phase 0) | 1068 | 1 pre-existing failure, 54 skipped |
| After all phases (Phase 12) | 1198 | +130 new tests, 1 same pre-existing failure, 58 skipped |

New test files (all in `tests/unit/` unless noted):

- `test_interval_registry_12h.py` (Phase 1)
- `test_exchange_rules_xmr_usdt.py` (Phase 1)
- `test_ta_utils_shim_parity.py` (Phase 2; skips if hummingbot not on path)
- `test_mr_bb_rsi_features.py` (Phase 2)
- `test_ema_regime_hold_features.py` (Phase 2)
- `test_ema_regime_hold_timestamp_leakage.py` (Phase 2 — D20 leak test)
- `test_mr_bb_rsi_controller_equivalence.py` (Phase 2; importorskip)
- `test_ema_regime_hold_controller_equivalence.py` (Phase 2; importorskip)
- `test_mr_bb_rsi_strategy.py` (Phase 3)
- `test_ema_regime_hold_strategy.py` (Phase 3)
- `test_mr_bb_rsi_engine_integration.py` (Phase 3)
- `test_ema_regime_hold_engine_integration.py` (Phase 3)
- `test_mr_bb_rsi_factory_registration.py` (Phase 4)
- `test_ema_regime_hold_factory_registration.py` (Phase 4)
- `test_factory_regression.py` (Phase 4)
- `test_search_space_mr_bb_rsi.py` (Phase 5)
- `test_search_space_ema_regime_hold.py` (Phase 5)
- `test_canonicalizer_mr_bb_rsi.py` (Phase 6)
- `test_canonicalizer_ema_regime_hold.py` (Phase 6)
- `test_objective_wrapper_mr_bb_rsi.py` (Phase 7)
- `test_objective_wrapper_ema_regime_hold.py` (Phase 7)
- `test_objective_wrapper_dispatch_regression.py` (Phase 7)
- `test_stress_mr_bb_rsi.py` (Phase 8)
- `test_stress_ema_regime_hold.py` (Phase 8)
- `test_mr_bb_rsi_walkforward.py` (Phase 9)
- `test_ema_regime_hold_walkforward.py` (Phase 9)
- `test_mr_bb_rsi_holdout.py` (Phase 9)
- `test_ema_regime_hold_holdout.py` (Phase 9)
- `test_export_mr_bb_rsi_yaml.py` (Phase 10)
- `test_export_ema_regime_hold_yaml.py` (Phase 10)
- `test_sweep_notebook_directional_generation.py` (Phase 11)
- `tests/integration/test_directional_e2e.py` (Phase 12; marked `slow`)

## Design Decisions Enforced

- **D1**: `timestamp_mode='open'` default on both feature configs.
- **D2**: `max_spread_pct` NOT enforced in backtest; passed through to YAML.
- **D3**: `max_trades_per_day` enforced in strategy via rolling 24h counter;
  fixed at 6 in search space (live-safety cap, not tuned).
- **D4**: `hold_mode='hold'` raises `NotImplementedError` at both strategy
  init AND canonicalize.
- **D5**: Both strategies are long-only; adversarial signal=-1.0 is rejected.
- **D6**: `latency_bars = 1` set by canonicalizers.
- **D7**: `executor_refresh_time = bar_interval_seconds` set by canonicalizers.
- **D9**: vectorized path is canonical; controller_compat flag retained for
  parity fixture generation only.
- **D10**: `"12h": 43200` added to INTERVAL_SECONDS.
- **D11**: 4h is the primary regime interval.
- **D12**: XMR-USDT rules hard-coded per the pre-verified table.
- **D13**: `available_quote_for_buy() < capital_per_entry * 0.99` rejects
  cleanly at the strategy layer.
- **D14**: signal arrays are float64 {0.0, 1.0, nan}.
- **D15**: Strategy registry keys are bare `"mean_reversion_bb_rsi"` and
  `"ema_regime_hold"`.
- **D16**: Export metadata uses `_v1` suffixes matching Hummingbot filenames.
- **D17**: `min_trend_slope` fixed at 0.0; non-zero inputs clamped (not
  rejected).
- **D18**: `volume_filter_window + 50 > required_records` → reject with
  informative string.
- **D19**: Slow/fast buffer guards reject configs that exceed the live
  controller's `max_records` limits.
- **D20**: Dedicated timestamp-leakage test (`test_ema_regime_hold_timestamp_leakage.py`)
  runs for both replay AND vectorized paths.

## Hummingbot YAML Export Paths (NonKYC XMR-USDT)

Assuming the notebook is configured with `CONNECTOR='nonkyc'`,
`TRADING_PAIR='XMR-USDT'`, and a given `STUDY_NAME`, the exported files are:

- MR: `artifacts/<STUDY_NAME>/nonkyc_xmr_usdt_mean_reversion_bb_rsi_v1.yml`
- EMA: `artifacts/<STUDY_NAME>/nonkyc_xmr_usdt_ema_regime_hold_v1.yml`

Both round-trip through `validate_export_*` and, when `hummingbot` is
available, through the live Pydantic controller models.

## Open Escalations

None.

## Deliverables Checklist

- [x] Exactly **four** pre-existing files modified (no more, no less).
- [x] All new modules under `pmm_lab/{features,strategies,optuna,objective,export}/`.
- [x] Every new module has a companion test file; no existing test file was
  edited.
- [x] Phase 0 baseline maintained: 1068 passing before → 1198 passing after,
  1 pre-existing failure unchanged.
- [x] All 13 phase reports exist in `artifacts/`.
- [x] No `hummingbot/` file modified.
- [x] No PMM Dynamic or MACD-BB code path altered.

## Status: COMPLETE
