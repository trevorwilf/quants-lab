# Phase 0 — Half-open session helper + instrumentation + MemoryBudget

Speedup report §3, §10.0, §11.1 / matrix doc §9.

## What landed

- **Half-open XNYS sessions helper** (`src/bowaka_v2_lab/optuna/calendar_sessions.py`,
  new). `calendar_sessions_half_open(start, end)` is now the single source of
  truth for `walkforward_runner._xnys_sessions` and `pit_universe._xnys_sessions`;
  both delegate to it. `preflight._probe_fold` also uses it.
  A fold whose `val_end == final_holdout_start` can no longer leak the
  holdout's first session into validation.
- **ProfileCounters** (`src/bowaka_v2_lab/utils/profile_counters.py`, new).
  Process-level flag + `ContextVar` instance. Counters default to `False`
  (zero overhead at call sites); enable via
  `with profile_counters_context(enable=True) as counters: ...`. Increments
  are wired into: minute-bar / forward-minute / quote suppliers, the daily
  cache builder, the event-loop dispatcher (`event_count_processed`), the
  scanner (`gate_dump_rows_constructed`), and atomic file writers
  (`artifact_bytes_written`). All guarded — no behaviour change when off.
- **MemoryBudget** (`src/bowaka_v2_lab/utils/memory_guard.py`, new).
  `MemoryReserveViolation` + `MemoryBudget(total_ram_gib, reserve_system_gib=32,
  max_optuna_workers=8, worker_private_gib_estimate=6, postgres_gib_estimate=8,
  emergency_headroom_gib=16)`. Methods: `from_system()`,
  `effective_bowaka_budget_gib()`, `projected_worker_use_gib()`,
  `assert_launch_safe(feature_store_gib_estimate, n_workers=None)`,
  `assert_available_reserve(reserve_gib=None)`. Wired by Phases 5/8/9.
- **Benchmark script** (`scripts/benchmark_optuna_objective.py`, new).
  Drives a 1-trial walk-forward against a synthetic tiny lake with counters
  on; writes JSON to `artifacts/benchmarks/phase_0_baseline.json` (gitignored)
  for later phase comparison.
- **Pre-existing Windows-platform fixes** (necessary to clear the gate so
  Phase 0 could run on the operator's Win11 machine):
  - `reference/import_config.py` — switched `dest.write_text` →
    `dest.write_bytes(...encode("utf-8"))` so the LF newlines pinned by
    `.gitattributes` survive Windows text-mode CRLF translation.
  - `tests/integration/test_optuna_storage_path.py` — replaced the
    POSIX-only `startswith("sqlite:////")` assertion with a platform-aware
    `_is_absolute_sqlite_uri()` helper that also accepts SQLAlchemy's
    Windows absolute form (`sqlite:///C:/...`).

## New tests

- `tests/unit/optuna/test_xnys_sessions_half_open.py` (8 tests).
- `tests/unit/utils/test_memory_guard.py` (10 tests).
- `tests/unit/utils/test_profile_counters.py` (9 tests).
- `tests/integration/test_walkforward_no_holdout_session_read_at_boundary.py` (1 test).

## Tests excluded by gate

- Live (`live_alpaca`, `live_paper`, `live_mongo`) and `slow`-marked tests
  are deselected per the `make test` definition in `Makefile`.

## Result

`make test` (full unit + parity + integration + reconcile, excluding
slow/live): **1154 passed, 0 failed, 12 deselected** (13:14).

## Branch

`feature/phase-0-halfopen-and-instrumentation` merged to `dev` with
`--no-ff`. Phase 1 (`feature/phase-1-objective-minimal`) takes off from
`dev` next.
