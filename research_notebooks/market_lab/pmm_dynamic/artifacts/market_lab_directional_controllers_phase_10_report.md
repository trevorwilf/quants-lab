# Phase 10 Report — Hummingbot YAML Export

**Date**: 2026-04-17

## Files Created

- `pmm_lab/export/hb_yaml_mr_bb_rsi.py`
  - `MRBBRSIExportParams` dataclass.
  - `export_mr_bb_rsi_yaml(strategy_config, engine_config, export_params, out_path)`.
  - `validate_export_mr_bb_rsi(yaml_path)` with Pydantic-mirrored constraints.
- `pmm_lab/export/hb_yaml_ema_regime_hold.py`
  - `EMARegimeHoldExportParams` dataclass.
  - `export_ema_regime_hold_yaml(...)`.
  - `validate_export_ema_regime_hold(...)` including `regime_ema_fast < regime_ema_slow`.

## Trailing Stop Format

Following the live template convention: empty string when disabled, else
`"<activation>/<delta>"`. This matches the YAML shape the controllers
parse at runtime (the controllers accept a string for trailing_stop).

## Tests Added

- `tests/unit/test_export_mr_bb_rsi_yaml.py` — 5 tests including trailing stop
  empty-string and formatted-string cases.
- `tests/unit/test_export_ema_regime_hold_yaml.py` — 4 tests including
  fast/slow ordering validator.

All 9 pass.

## Phase 10 — Complete
