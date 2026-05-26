# Phase 2 — Parallel preflight + workstation hardware profile

Speedup report v2 §1.3, §4 P2 and P5, §5.4, §5.5, §10.3, §11.2 Phase 2.

## What landed

- **`preflight_parallel_dispatch(...)`** + `ParallelDecision` in
  `optuna/parallel.py`. The pre-remediation flow ran storage + memory
  viability checks **inside** `run_bowaka_optimization_dispatch` —
  AFTER the parent had already built fold contexts. The Phase 2 helper
  bubbles them up so a strict-parallel run against SQLite, or with a
  memory budget that cannot fit the requested worker count, fails
  closed BEFORE the parent pays the context-build cost.
  * `n_jobs <= 1` → `serial`, no further checks.
  * `n_jobs > 1` + SQLite / in-memory storage → raises
    `OptunaStudyInvalidError` (unconditional; concurrent SQLite writers
    corrupt the DB regardless of `strict_parallel`). The only escape
    is `n_jobs == 1`.
  * Memory refusal: `strict_parallel` raises; otherwise returns
    `serial` with the violation reason.
- **`run_walkforward_study` refactored** to call the helper BEFORE
  `build_fold_contexts(...)`. In `process_parallel` mode the parent
  SKIPS the context build entirely — each worker rebuilds via the
  dotted factory. The objective is bound to a stub
  `_stub_parent_objective_for_parallel` that raises if the dispatcher
  ever calls it in-parent (defence-in-depth). `study.user_attrs`
  records `dispatch_mode` / `dispatch_reason` / `dispatch_n_workers`.
- **Failed-study artifact written on parallel-preflight refusal** —
  same contract as the Phase 0 DQ short-circuit + Phase 0 structural
  escape. Includes the phase-profile JSON for forensic time
  attribution.
- **`ProfileCounters.parallel_preflight_seconds`** (float, cumulative
  seconds across studies in a process) — bumped via the existing
  default-off counter context.
- **Workstation overlay configs** (Phase 2 task 3):
  * `configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml`
    — 8-worker base profile. `memory_reserve_gib=62`,
    `strict_parallel=true`, `max_workers=8`, `blas_thread_pin=true`,
    `n_jobs=8`.
  * `.workstation_10w.yml`, `.workstation_12w.yml`,
    `.workstation_16w.yml` — benchmark-only overlays at the same
    workstation profile with the worker count bumped. Each carries an
    explicit "do NOT promote a study built with this overlay until a
    workstation benchmark proves wall-clock improvement vs the 8w
    baseline" warning header.
  * Base `bowaka_v2_actual_iex_current_code_optuna.yml` UNCHANGED
    (`memory_reserve_gib=32`, `strict_parallel=false`,
    `max_workers=8`).
- **`scripts/benchmark_optuna_workers.py`** (new) — operator-driven
  sweep over `--workers 1,4,8,10,12,16`. Writes
  `artifacts/benchmarks/phase_2_workers_<N>.json` per run + a
  `phase_2_workers_summary.json`. Not asserted by any test.

## New tests

- `tests/unit/optuna/test_preflight_parallel_dispatch_storage_check.py`
  (4): SQLite + parallel raises in both strict_parallel modes;
  None URI + parallel raises; serial-on-SQLite is allowed;
  PostgreSQL + budget returns process_parallel.
- `tests/unit/optuna/test_preflight_parallel_dispatch_memory_check.py`
  (3): 8 workers fit the workstation budget; 50 workers under
  strict_parallel raises; 50 workers without strict_parallel falls
  back to serial.
- `tests/unit/optuna/test_memory_budget_workstation_arithmetic.py` (6):
  effective Bowaka budget = 106 GiB; 8/10/12/16 workers all fit;
  50 workers fails closed.
- `tests/unit/optuna/test_workstation_overlays_load_and_validate.py` (4):
  the 4 overlay configs load + carry the operator-specified
  `memory_reserve_gib=62`, `strict_parallel=true`, `blas_thread_pin=true`
  fields; the 10/12/16w overlays differ only in `max_workers` /
  `n_jobs`.
- `tests/unit/optuna/test_parallel_preflight_writes_failed_artifact.py`
  (1): strict_parallel + SQLite raises and the failed-status study
  artifact lands on disk before the exception propagates.
- `tests/integration/test_strict_parallel_skips_parent_context_build.py`
  (1): with a stubbed-PG preflight decision the parent never invokes
  `build_fold_contexts`.
- `tests/integration/test_serial_fallback_still_builds_context_once.py`
  (1): `n_jobs=1` runs the legacy path — context built once, study
  completes ok.
- `tests/integration/test_strict_parallel_fails_before_context_build.py`
  (1): strict_parallel + SQLite raises and never calls
  `build_fold_contexts` (asserted by a patched assertion).

## Tests

| Gate | Result | Time |
|---|---|---|
| `make test-fast` | **992 passed**, 0 failed | 41.2s |
| `make test-integration` (timeout=300) | **333 passed**, 2 skipped (PG-gated), 13 deselected (live + slow) | 13:51 |

## Default-off discipline

- Base config `bowaka_v2_actual_iex_current_code_optuna.yml` is
  untouched: `memory_reserve_gib=32`, `strict_parallel=false`,
  `max_workers=8` — same as pre-Phase-2.
- Workstation overlays are explicit operator opt-ins; no CI / default
  command path picks them up.
- `parallel_preflight_seconds` increments only when
  `_COUNTERS_ENABLED` is true (the runner binds the counter context
  for its duration, so studies record their preflight cost
  automatically).

## Branch

`feature/phase-2-parallel-preflight-and-profile` — merged to `dev` with
`--no-ff`.
