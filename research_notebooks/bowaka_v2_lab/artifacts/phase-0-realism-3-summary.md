# Phase 0 — Audit landing + P0 stop-ship code patches

**Branch:** `phase-0-realism-3-p0-stopship` off `dev`.
**Audit findings addressed:** P0-001 (all-sentinel success), P0-002 (interval semantics), P0-003 (DQ/quote fail-open).

## Verification of pre-remediation defects

| Defect | File | Status |
|---|---|---|
| P0-002 closed-interval guard | `src/bowaka_v2_lab/optuna/holdout_guard.py:34` | confirmed, fixed |
| P0-001 sentinel-only success | `src/bowaka_v2_lab/optuna/walkforward_runner.py:78, 592` | confirmed, fixed |
| P0-003 DQ/quote fail-open | `src/bowaka_v2_lab/optuna/preflight.py:130/214` | confirmed, fixed |

## Changes

### 0.0 — Audit landing
- `research_notebooks/bowaka_v2_lab/docs/audits/2026-05-23_realism_audit.md` — new file mirroring the remediation-3 prompt's `Critical context` plus a structured P0/P1/P2 table + reproductions.
- `README.md` — new `Active audit blockers (2026-05-23)` section pointing at the audit and listing every P0/P1 with its remediation phase.

### 0.1 — Structural exception taxonomy
- `src/bowaka_v2_lab/optuna/errors.py` — new module with `OptunaStudyInvalidError`, `ConfigParityError`, `MissingLakePartitionError`, `STRUCTURAL_EXCEPTIONS`, and `structural_exceptions()` (lazy late-binding to avoid import cycles).
- `src/bowaka_v2_lab/data/data_quality.py` — added `class DataQualityError(RuntimeError)`. The report-returning API is unchanged.

### 0.2 — Half-open HoldoutGuard (P0-002)
- `src/bowaka_v2_lab/optuna/holdout_guard.py:30-56` — `assert_can_read` switched to half-open `[start, end)` semantics. `end == final_holdout_start` and `start == final_holdout_end` are now allowed; any true overlap still raises.
- `src/bowaka_v2_lab/optuna/walkforward.py` — `WalkForwardSplit` / `WalkForwardPlan` docstrings updated to state the half-open convention. The planner's `if val_end > final_start: break` is already half-open-consistent (no change to behavior).

### 0.3 — Structural exceptions un-degradable (P0-001 root cause)
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::_run_validation_folds` — added `except STRUCTURAL_EXCEPTIONS: raise` BEFORE the broad `except Exception` that degrades to `_degraded_fold(fold_id)`. Non-structural strategy/eval errors still degrade.
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::make_walkforward_objective` — same pattern in the per-trial objective closure: structural exceptions propagate, non-structural still become `_FAILED_TRIAL_SCORE`.

### 0.4 — Validate the completed-trial set (P0-001)
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::run_walkforward_study` — wraps `study.optimize(...)` in `try: ... except structural as struct_exc:` that writes a `status: "failed"` artifact and raises `OptunaStudyInvalidError`.
- After `study.optimize` returns, the runner builds `valid_trials` / `invalid_trials` lists. A trial is **invalid** when its value is at or below `_FAILED_TRIAL_SCORE + 1e-6` (sentinel) OR when its `fold_scores` / `fold_metrics` user_attrs don't match `len(plan.splits)` (missing fold metrics). If every completed trial is invalid the runner writes a failed artifact and raises `OptunaStudyInvalidError`.
- `_write_failed_study_artifact(...)` — new helper that emits the same `<study>.json` path the success path would have used, with `status: "failed"`, `failure_reason`, `best_params: {}`, `best_trial_report: {"error": ...}`, and the full `study_metadata` for forensic review.

### 0.5 — Harden intended-realism preflight (P0-003)
- `src/bowaka_v2_lab/optuna/preflight.py::_check_data_quality` — `dq_report is None` under `intended_realism` now returns `status="fail"` (was `skipped`). Parity / smoke retain the previous `skipped`.
- `src/bowaka_v2_lab/optuna/preflight.py::_check_quote_coverage` — same fix for `quote_coverage_pct is None`.
- `src/bowaka_v2_lab/optuna/preflight.py::_check_sip_data` — `present is None` under `intended_realism` now returns `status="fail"` (records the underlying probe exception in evidence). Parity / smoke retain `skipped`.
- `src/bowaka_v2_lab/optuna/preflight.py::_probe_fold` — calendar / DQ / quote probe exceptions all return `status="fail"` under `intended_realism`; parity / smoke retain the prior `skipped` fold result.
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::run_walkforward_study` — preflight-probe block keeps `dq_report=None` / `quote_cov_pct=None` on probe failure; the updated `_check_*` helpers turn that into a hard fail under `intended_realism`.

### 0.6 — Tests
- `tests/unit/optuna/__init__.py` — new package directory for the audit-specific Optuna unit tests.
- `tests/unit/optuna/test_holdout_guard_boundaries.py` — 8 new tests pinning the half-open semantics (boundary-equal allowed, true overlap blocked, bracket-blocked, one-day-into-holdout-blocked, etc.).
- `tests/unit/optuna/test_preflight_fail_closed.py` — 22 new tests covering DQ / quote / SIP / `_probe_fold` fail-closed semantics per simulation mode and the end-to-end `run_preflight` contract.
- `tests/integration/test_walkforward_runner.py::test_run_walkforward_study_real_backtests` — strengthened with `best_value > -1e9 + 1e-6` and `len(fold_metrics) == n_folds` and `median_fold_score is not None` assertions.
- `tests/integration/test_walkforward_runner_invalid_study.py` — 3 new tests: all-sentinel scenario raises `OptunaStudyInvalidError`; structural exception raises the same; the failed artifact contains study metadata.
- `tests/integration/test_optuna_preflight_refuses_low_quote_coverage.py::test_probe_quote_coverage_none_supplier_returns_none` — updated to assert the new fail-closed behavior under `intended_realism` AND the preserved `skipped` behavior under `current_code_parity`.

## Test results

| Group | Result |
|---|---|
| `tests/unit + tests/parity` | 749 passed, 0 failed |
| `tests/integration + tests/reconcile` | 316 passed, 1 skipped, 12 deselected, 0 failed |
| `bowaka_common` | 97 passed, 0 failed |
