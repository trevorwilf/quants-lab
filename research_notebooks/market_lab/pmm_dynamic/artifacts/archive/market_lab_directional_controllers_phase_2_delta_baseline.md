# Phase 2 Delta Baseline

**Date**: 2026-04-17
**Prerequisite confirmation**: phase-1 artifacts present (FINAL.md and phase
reports 0..12), strategy modules exist, `create_sweep_nb_directional.py`
exists.

## Baseline Test Suite

Command:
```
pytest tests/ -q --ignore=tests/integration/test_mongo_live.py --ignore=tests/integration/test_optuna_smoke.py
```

Result: **1198 passed, 58 skipped, 1 failed, 24 warnings** in 109.39s.

The single failure is the same pre-existing `test_run_full_pipeline_mini`
(PMM Dynamic canonicalizer path, not touched by phase-1 or this delta).

Matches the phase-1 FINAL.md counts exactly. Ready to proceed with
delta changes.
