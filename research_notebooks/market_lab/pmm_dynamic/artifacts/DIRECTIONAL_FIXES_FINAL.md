# Directional Pipeline Fixes — FINAL

**Date**: 2026-04-17
**Scope**: All 12 ML-DIR findings across Phase 1 (fail-closed), Phase 2 (reproducibility), Phase 3 (architecture).

## Test counts

| Moment | Passed | Skipped | Failed |
|---|---|---|---|
| Pre-work baseline (prompt ref) | ~1252 | ~58 | 0 |
| Final (end of Phase 3) | **1424** | 59 | 0 |

Net delta: **+172 tests** across all three phases.

## Phase 1 — fail-closed (Critical)

| Item | Finding | Status |
|---|---|---|
| P1.0 | Quarantine legacy `_build_from_pmm.py` | Moved to `_legacy/_build_from_pmm_LEGACY_DO_NOT_USE.py` with raise-on-import guard |
| P1.1 | ML-DIR-010: `MongoCandleLoader.load()` doesn't exist | Fixed to `load_range(DataQuery(...))`; added `DataQuery` import |
| P1.2 | ML-DIR-004: directional walk-forward silently always skipped | Added `pmm_lab/objective/walkforward_dispatch.py` using `run_simulation` dispatch |
| P1.3 | ML-DIR-001: fail-open notebook status | Validation state machine (optimized_only / validated_pass / validated_fail / validation_error) + YAML goes to `.pending/` first, moved to `rejected/` + REJECTED.json on failure |
| P1.4 | ML-DIR-003: stale cells 12/14 raise KeyError | Rewrote via `scripts/patch_direction_custom_notebooks.py`; use `.get()` fallbacks and `robust_score` |
| P1.5 | Minor cleanup | Renamed `Time` header → `DataDays`; added cell IDs via `nbformat.validator.normalize` |

**Phase 1 gate: 42 tests pass.**

## Phase 2 — reproducibility (High)

| Item | Finding | Status |
|---|---|---|
| P2.1 | ML-DIR-002: EMA `dataset_hash` misses regime stream | Added `pmm_lab/data/ema_identity.py` + regime-aware cache key via `_dataset_key_for` |
| P2.2 | ML-DIR-006: PMM-centric sensitivity perturbation | Added `MR_PERTURBABLE_PARAMS` + `EMA_PERTURBABLE_PARAMS` with signal hyperparams |
| P2.3 | ML-DIR-009: no directional parity fixtures | `check_feature_parity_frozen_mr/_ema` + `generate_directional_fixtures.py` + `fixtures/{mr,ema}_short_100bar/` committed |
| P2.4 | ML-DIR-007: `max_trades_per_day_binding_fraction` misnomer | Renamed to `total_reject_fraction`; kept old key as deprecation alias |

**Phase 2 gate: 21 tests pass.**

## Phase 3 — architecture (Medium)

| Item | Finding | Status |
|---|---|---|
| P3.1 | ML-DIR-008: `hold_mode='hold'` un-backtested | Both strategy-specific and generic validators reject `hold_mode='hold'` |
| P3.2 | ML-DIR-011: no notebook-execution CI | Added `test_cell10_compact_table_execution.py` + `test_sweep_nb_generator_smoke_execution.py` |
| P3.3 | ML-DIR-012: eager strategies/__init__.py pulls pandas_ta | PEP 562 lazy `__init__.py` + `_module_is_installable` helper in `runner_dispatch.py` and `signal_cache.py` distinguishes missing vs broken modules |

**Phase 3 gate: 22 tests pass.**

## Files modified

| File | Change |
|---|---|
| `create_sweep_nb_directional.py` | Loader call uses `load_range(DataQuery(...))`; added DataQuery import |
| `notebooks/direction-custom/_build_cell8.py` | Walk-forward via `walkforward_dispatch`; validation state machine; EMA composite identity; MR/EMA perturb lists; parity calls use `_mr/_ema` variants |
| `notebooks/direction-custom/_build_cell10.py` | Filters on `validation_status`; secondary `REJECTED CANDIDATES` table; `DataDays` header |
| `notebooks/direction-custom/*.ipynb` (×4) | Cell 8 regenerated; cells 10, 12, 14 rewritten; stable cell IDs |
| `pmm_lab/objective/signal_cache.py` | Regime-aware `_dataset_key_for`; `_module_is_installable` helper; converted 5 `except ImportError: pass` to fail-explicit pattern |
| `pmm_lab/objective/walkforward_dispatch.py` (new) | Strategy-dispatched walk-forward via `run_simulation` |
| `pmm_lab/sim/runner_dispatch.py` | `_module_is_installable` helper; converted 4 `except ImportError: pass` |
| `pmm_lab/strategies/__init__.py` | PEP 562 lazy module (no eager submodule imports) |
| `pmm_lab/optuna/sensitivity.py` | Added `MR_PERTURBABLE_PARAMS`, `EMA_PERTURBABLE_PARAMS` |
| `pmm_lab/optuna/objective_wrapper_mr_bb_rsi.py` | Emits `total_reject_fraction` (+ old alias) |
| `pmm_lab/parity/feature_parity.py` | Added `check_feature_parity_frozen_mr`, `check_feature_parity_frozen_ema`, `_compare_fields` helper |
| `pmm_lab/parity/fixtures.py` | `FrozenFixture.regime_candles` optional field; supports `.npy`/`.npz`; `expected_features.json` + `config_params.json` layout |
| `pmm_lab/export/hb_yaml_ema_regime_hold.py` | `hold_mode='hold'` raises ValueError (was warning) |
| `pmm_lab/export/validate_export.py` | Dispatches to `_validate_ema_regime_hold_mirror` + `_validate_mean_reversion_bb_rsi_mirror` |
| `tests/unit/test_signal_cache_key_dataset_scope.py` | Pre-existing test using real SimConfig (no change needed this phase — kept working) |
| `tests/unit/test_direction_custom_cell10_compact_table.py` | Column renamed Time → DataDays |
| `tests/unit/test_direction_custom_notebooks_config_sanity.py` | MR TOP_N now accepts any int (user set to 15) |

## Files created

| File | Purpose |
|---|---|
| `pmm_lab/data/ema_identity.py` | Composite EMA dataset identity (P2.1) |
| `pmm_lab/objective/walkforward_dispatch.py` | Strategy-dispatched walk-forward (P1.2) |
| `scripts/generate_directional_fixtures.py` | Generates MR + EMA fixtures (P2.3) |
| `scripts/patch_direction_custom_notebooks.py` | Rewrites cells 12/14 (P1.4) |
| `fixtures/mr_short_100bar/` | MR parity fixture (candles, expected_features, config) |
| `fixtures/ema_short_100bar/` | EMA parity fixture (+ regime_candles) |
| `tests/unit/test_sweep_nb_directional_generator_runtime.py` | ML-DIR-010 runtime guard |
| `tests/unit/test_walkforward_dispatch.py` | Walk-forward dispatch smoke tests |
| `tests/unit/test_direction_validation_state_machine.py` | ML-DIR-001 state machine |
| `tests/unit/test_direction_custom_cells_12_14_execute.py` | ML-DIR-003 cells 12/14 runtime |
| `tests/unit/test_ema_dataset_identity.py` | ML-DIR-002 composite identity |
| `tests/unit/test_sensitivity_directional_params.py` | ML-DIR-006 directional perturb |
| `tests/unit/test_directional_parity.py` | ML-DIR-009 fixtures + parity |
| `tests/unit/test_reject_fraction_rename.py` | ML-DIR-007 rename |
| `tests/unit/test_ema_hold_mode_export_block.py` | ML-DIR-008 export block |
| `tests/unit/test_cell10_compact_table_execution.py` | ML-DIR-011 cell 10 runtime |
| `tests/unit/test_sweep_nb_generator_smoke_execution.py` | ML-DIR-011 generator smoke |
| `tests/unit/test_import_isolation.py` | ML-DIR-012 lazy init |

## Escalations

None.

## Out of scope (per prompt)

- Hold-mode simulation parity (ML-DIR-008 option 1) — only export-side block installed
- `finalist_validation.py` full refactor (ML-DIR-005 full resolution)
- Per-reason rejection counts in `SimResult` (ML-DIR-007 full resolution)
- Paper-trade drift monitoring and deployment-readiness items

## Handoff verification checklist

For Trevor to run after this lands:

1. Run a real sweep end-to-end; verify a `validated_fail` candidate's YAML is under `rejected/` with REJECTED.json sibling
2. An EMA run's `result_entry` has `composite_hash` ≠ `signal_hash`
3. MR and EMA sensitivity penalties are visibly higher (signal-hyperparam fragility)
4. `pytest tests/unit/test_export_mr_bb_rsi_yaml.py` collects cleanly (P3.3)
5. `grep -rn "loader\.load(" notebooks/ create_sweep_nb_directional.py` returns no hits (except legacy)
6. Cell 12 and cell 14 execute cleanly on real sweep_results without KeyError

## Status: COMPLETE
