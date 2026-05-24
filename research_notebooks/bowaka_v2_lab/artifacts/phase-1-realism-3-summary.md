# Phase 1 — Full-PIT preflight + lake verification CLI

**Branch:** `phase-1-realism-3-full-pit-preflight` off `dev`.
**Audit findings addressed:** §6.6 (capped preflight), P0-004/P0-005 (lake completeness verification only — ingestion is out of scope), P1-001 (PIT-universe coverage telemetry).

## Changes

### 1.1 — Full per-fold PIT eligible-universe union
- `src/bowaka_v2_lab/optuna/pit_universe.py` — new module with `fold_pit_symbol_union` (iterates exchange-calendar sessions in the half-open ``[start, end)`` window and unions the eligible symbols via `build_pit_universe_for_sessions`) and `plan_pit_symbol_union` (rolls up across every fold + the final-holdout window).
- Uses the same half-open convention as the planner / guard (audit §P0-002).

### 1.2 — `_resolve_symbols` honors intended_realism
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::_resolve_symbols` now accepts `sim_mode` and `plan` and, under ``intended_realism`` (with `optuna.preflight.research_waiver_capped_symbols: false`), returns the full PIT union. Parity / smoke / explicit-waiver paths keep the capped 100-symbol behaviour.
- `run_walkforward_study` passes `sim_mode=sim_cfg.mode, plan=plan` when invoking `_resolve_symbols`.

### 1.3 — Coverage telemetry
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::run_walkforward_study` computes `pit_union_symbol_count`, `preflight_coverage_fraction`, and `research_waiver_capped_symbols`. Under ``intended_realism`` without a waiver and coverage < 1.0 the runner raises `PreflightError` listing the missing symbol delta.
- These three fields are surfaced in `study.universe.*` in the success artifact AND in the failed-status artifact (`_write_failed_study_artifact` signature extended).

### 1.4 — `bowaka-v2-lab verify-lake` CLI
- `src/bowaka_v2_lab/data/verify_lake.py` — new module with `verify_lake()` and `verify_lake_or_raise()` (raises `MissingLakePartitionError`).
- Checks: daily bars / minute bars (per feed), quotes (per feed), statuses, corporate actions, asset snapshots, manifest adjustment (not `raw` under intended_realism). A single asset snapshot warns rather than fails — P1-001 tracks the historical-snapshot ingestion separately.
- `src/bowaka_v2_lab/cli.py::_cmd_verify_lake` wires the function to a CLI subcommand `verify-lake [--lake PATH] [--feed iex|sip] [--intended-realism]`. Exits non-zero under `--intended-realism` when any required check fails. Emits a structured JSON document on stdout.

### 1.5 — Tests
- `tests/unit/optuna/test_pit_universe_union.py` — 6 tests pinning the union semantics (3-session union, ineligible-symbol drop, half-open boundary, None-lake guard, plan union with/without holdout).
- `tests/unit/optuna/test_full_pit_preflight_fail_closed.py` — 5 tests pinning `_resolve_symbols` per simulation mode + waiver behaviour.
- `tests/integration/test_verify_lake_cli.py` — 6 CLI tests: complete-lake pass, partial-lake fail (intended_realism), partial-lake warn (no intended_realism), raw-manifest fail, one-snapshot warn, multi-snapshot pass.

## Test results

| Group | Result |
|---|---|
| `tests/unit + tests/parity` | 760 passed (+11 vs Phase 0), 0 failed |
| `tests/integration + tests/reconcile` | 322 passed, 1 skipped, 12 deselected, 0 failed |
| `bowaka_common` | 97 passed (unchanged) |
