# Phase 12 Report — End-to-End Smoke Test

**Date**: 2026-04-17

## Files Created

- `tests/integration/test_directional_e2e.py` — marked `@pytest.mark.slow`,
  exercises the full pipeline for both strategies:
  1. `create_objective()` → run 2 trials
  2. Pick best non-rejected trial, canonicalize its params
  3. Export YAML
  4. Validate round-trip via `validate_export_*`

Both MR and EMA smoke tests pass.

## Full Suite Comparison

| Metric | Phase 0 Baseline | Phase 12 After |
|---|---|---|
| Passed | 1068 | **1198** (+130) |
| Skipped | 54 | 58 (+4) |
| Failed | 1 (pre-existing) | 1 (same pre-existing) |
| Runtime | 102.60s | 105.94s |

The pre-existing failure (`test_run_full_pipeline_mini`) is unchanged — it
fails on `KeyError: 'total_amount_quote'` in `pmm_lab/optuna/canonicalizer.py`,
which is a PMM-Dynamic canonicalizer path the prompt explicitly forbids us
from modifying.

## Phase 12 — Complete
