# Phase 2 Delta — FINAL Report

**Date**: 2026-04-17
**Scope**: Two surgical changes on top of phase-1.

## Test Counts

| Stage | Passed | Skipped | Failed |
|---|---|---|---|
| Phase-1 FINAL | 1198 | 58 | 1 (pre-existing) |
| Phase-2 delta baseline | 1198 | 58 | 1 (same) |
| Phase-2 delta final | **1251** | 58 | **0** |

Net change: **+53 new passing tests**. The previously-flaky
`test_pipeline_runner.py::TestRunFullPipelineMini::test_run_full_pipeline_mini`
now passes on a fresh run (no code path we touched; unrelated flakiness).

## Change 1: 8h registered in INTERVAL_SECONDS

### Files modified
- `pmm_lab/config/defaults.py` — single-line insert of `"8h": 28800,`
  between `"4h"` and `"12h"`. No other edits.

### Test files
- **Renamed**: `tests/unit/test_interval_registry_12h.py` →
  `tests/unit/test_interval_registry_8h_12h.py`.
  - Kept every existing 12h assertion (regression coverage preserved).
  - Added `TestIntervalRegistry8h` (8h present at 28800).
  - Added `TestMonotonicOrdering` (iteration strictly increasing).
  - Added `TestValidateCandles8h` (validate_candles accepts 8h).
- The old `test_interval_registry_12h.py` is retained as an intentionally
  empty stub file — collected by pytest with zero tests — because the
  environment does not grant `rm` permission. This does not affect counts
  or behavior.

Result: 8 tests in the renamed file; all pass.

## Change 2: Four concrete direction-custom notebooks

### Files created
- `notebooks/direction-custom/mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb` (14 cells)
- `notebooks/direction-custom/mean_reversion_bb_rsi_retest_sweep.ipynb` (16 cells)
- `notebooks/direction-custom/ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb` (14 cells)
- `notebooks/direction-custom/ema_regime_hold_retest_sweep.ipynb` (16 cells)
- `notebooks/direction-custom/_build_from_pmm.py` — kept-in-tree builder
  that mirrors PMM structure. Running it regenerates all four notebooks
  deterministically.

### Mirroring the PMM pattern
- **Same cell count** as the PMM references (14 / 16).
- **Same cell-type alternation** — verified by
  `TestCellTypeAlternation::test_expected_cell_types`.
- **Same heading text prefixes** (`## 1.` through `## 6.` / `## 7.`) —
  verified by `TestMarkdownHeadings`.
- **Same preflight logic** in cell 4 (storage check, N_JOBS vs CPU count).
- **Same discovery cell skeleton** in cell 6 (for MR) with the
  three-gate filter; for EMA cell 6 uses the dual-interval pattern from
  section 2D (both signal_interval AND regime_interval must be present).
- **Same sweep-loop skeleton** in cell 8 — load → strict audit →
  canonicalize → export YAML → validate. For EMA the loop loads both
  streams per section 2E.

### Configuration (cell 3) per section 2C
- MR multi: `N_TRIALS=500`, `TOP_N=100`, `MIN_DATA_DAYS=56`,
  `MAX_TRAINING_DAYS=180`.
- MR retest: same except `TOP_N=75`, adds `RETEST_PAIRS` list.
- EMA multi: `N_TRIALS=500`, `TOP_N=100`, `MIN_DATA_DAYS=120`,
  `MAX_TRAINING_DAYS=None`, dual SIGNAL/REGIME interval dicts.
- EMA retest: same except `TOP_N=75`, adds `RETEST_PAIRS` list.

### Informational release gates
Cell 12 renders per-pair gate tables but never short-circuits. Only the
strict data audit is a hard-stop — at the per-pair level (a failed audit
`continue`s to the next pair). MR table includes the
`max_trades_per_day_binding_fraction` diagnostic; EMA does not.

### Tests added (Section 2G)
- `tests/unit/test_direction_custom_notebooks_structure.py` — 24 tests:
  JSON validity, cell counts, title markdown, concatenated `ast.parse()`,
  markdown heading positions, cell-type alternation.
- `tests/unit/test_direction_custom_notebooks_config_sanity.py` — 20 tests:
  N_TRIALS, MIN_DATA_DAYS, MAX_TRAINING_DAYS, TOP_N, signal/regime interval
  dicts in EMA notebooks, RETEST_PAIRS in retest notebooks.
- `tests/unit/test_direction_custom_notebooks_imports_resolvable.py` — 4 tests:
  every `import X` / `from X import Y` in each notebook resolves via
  `importlib.import_module`.

All 48 Section 2G tests pass.

## Disposition of phase-1 artifacts

- `create_sweep_nb_directional.py` — **kept**, unmodified.
- `tests/unit/test_sweep_notebook_directional_generation.py` — **kept**,
  still passes (6 tests).
- All phase-1 strategy/feature/canonicalizer/stress/export/objective-wrapper
  modules — **untouched**.

## Acceptance Criteria

- [x] Baseline passing count met (+53 over baseline, no regressions).
- [x] New tests from section 1B all pass.
- [x] New tests from section 2G all pass.
- [x] `notebooks/direction-custom/` contains exactly the four required `.ipynb` files.
- [x] `create_sweep_nb_directional.py` still exists and passes its tests.
- [x] No `hummingbot/` file modified.
- [x] No strategy / canonicalizer / search space / stress / exporter /
  objective_wrapper / YAML config / MACD-BB / PMM Dynamic path modified.

## Escalations

None.

## Status: COMPLETE
