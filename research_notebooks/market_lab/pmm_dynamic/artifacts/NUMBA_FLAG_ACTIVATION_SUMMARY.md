# Numba kernel flag activation in notebooks — Summary

**Date**: 2026-04-18

## Test counts

| Moment | Passed | Skipped | Failed |
|---|---|---|---|
| Pre-work baseline | 1466 | 59 | 0 |
| After flag activation (9 new unit tests) | 1474 | 59 | 0 |
| Plus 2 integration parity tests | +2 passed | — | 0 |

Net: **+11 tests** passing, zero regressions.

## Files modified

| File | Lines changed | Purpose |
|---|---|---|
| `notebooks/direction-custom/_legacy/_build_cell8.py` | ~8 lines | Added `USE_NUMBA_KERNEL = True` constant; threaded `use_numba_kernel=USE_NUMBA_KERNEL` into all 6 directional `_replace(...)` sites + both `compute_sensitivity(...)` calls |
| `pmm_lab/optuna/sensitivity.py` | ~15 lines | New `use_numba_kernel: Optional[bool] = None` kwarg on `compute_sensitivity`; threaded through both internal `replace(..., controller_compat=...)` sites |
| `notebooks/direction-custom/*.ipynb` (×4) | ~12 lines each | Cell 3 gets the `USE_NUMBA_KERNEL = True` constant; cell 8's 4 directional `_replace` + `compute_sensitivity` sites gain the flag |

## Files created

| File | Purpose |
|---|---|
| `scripts/enable_numba_in_notebooks.py` | Re-runnable surgical patcher for the 4 `.ipynb` notebooks |
| `tests/unit/test_numba_flag_integration.py` | 5 flag-propagation unit tests (parametrized over 4 notebooks → 9 total) |
| `tests/integration/test_numba_flag_end_to_end_parity.py` | 2 end-to-end mini-sweep parity tests (MR + EMA) |
| `artifacts/NUMBA_FLAG_ACTIVATION_SUMMARY.md` | This file |

## `_replace` sites updated

Breakdown per notebook (and in `_legacy/_build_cell8.py`):

| Site | MR | EMA | Where |
|---|---|---|---|
| Phase-2 dedup (`sc = _replace(bundle.strategy_config, controller_compat=PHASE2_CONTROLLER_COMPAT)`) | ✓ | ✓ | cell 8 |
| Validation (`val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT, …)`) | ✓ | ✓ | cell 8 |
| Holdout extras (`tc_cfg = _replace(tc_bundle.strategy_config, controller_compat=VALIDATION_CONTROLLER_COMPAT, …)`) | ✓ | ✓ | cell 8 |
| `compute_sensitivity(..., use_numba_kernel=USE_NUMBA_KERNEL)` | ✓ | ✓ | cell 8 |
| `sensitivity.py::compute_sensitivity` internal `replace(baseline_config, ...)` | — | — | sensitivity.py |
| `sensitivity.py::compute_sensitivity` internal `replace(config, ...)` in perturbation loop | — | — | sensitivity.py |

Total directional `_replace` sites threaded: **6 in `_build_cell8.py` + 2 `compute_sensitivity` kwargs + 2 internal `replace`s in sensitivity.py = 10 sites**.

`deploy/runner.py`, `holdout.py`, `walkforward_dispatch.py`: no directional `_replace` calls — grep'd, no change needed.

## Test pass/fail per section

- **Unit tests** (`tests/unit/test_numba_flag_integration.py`): **9/9 pass**
  - `test_notebook_cell_code_enables_numba_flag`
  - `test_committed_notebook_has_flag_enabled` (×4 parametrized)
  - `test_numba_flag_propagates_through_compute_signals_mr`
  - `test_numba_flag_propagates_through_compute_signals_ema`
  - `test_numba_flag_off_by_default_on_dataclass`
  - `test_numba_flag_off_produces_pandas_path`
- **Integration tests** (`tests/integration/test_numba_flag_end_to_end_parity.py`): **2/2 pass**
  - `test_mini_sweep_mr_numba_on_matches_numba_off_signals`
  - `test_mini_sweep_ema_numba_on_matches_numba_off_signals`
- **Full unit suite**: 1474 passed, 0 new failures.
- **Pre-existing Numba parity tests** (`test_numba_kernel_parity.py`): 19/19 still pass.

## Confirmation

The notebook constant `USE_NUMBA_KERNEL` is now `True`; the flag propagates from strategy config → feature config → kernel dispatch; bit-exact signal parity is verified end-to-end (bool arrays exact; float arrays within Stage 1's documented per-indicator tolerances; winner and robust_score match within rtol=1e-6).

Next production sweep will hit the **247x/3549x** warm-call Numba speedup measured in Stage 1 without any further operator action.

## Library-default preservation (confirmed)

```python
MRBBRSIFeatureConfig().use_numba_kernel          # → False
EMARegimeHoldFeatureConfig().use_numba_kernel     # → False
MeanReversionBBRSIStrategyConfig().use_numba_kernel   # → False
EMARegimeHoldStrategyConfig().use_numba_kernel        # → False
```

The notebook opts in via `USE_NUMBA_KERNEL = True` as a top-level constant, not a library-default change.
