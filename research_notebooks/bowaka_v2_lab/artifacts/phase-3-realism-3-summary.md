# Phase 3 — Storage path + stale defaults + risk-control promotion gate

**Branch:** `phase-3-realism-3-storage-defaults-promotion-gate` off `dev`.
**Audit findings addressed:** P1-006 (CWD-sensitive SQLite), P2-001 (stale defaults), P1-004 (risk-control promotion gate; user chose "leave search space, refuse promotion on drift"), P1-008 (IEX caveat — revalidated), P2-002 (segmentation hygiene markers).

## Changes

### 3.1 — Storage path resolution
- `src/bowaka_v2_lab/optuna/storage_path.py` — new module with `resolve_storage_uri(raw, *, paths)`. PostgreSQL URIs pass through unchanged; relative SQLite URIs are repointed at an absolute path under `paths.lab_root` and the parent directory is created. Special-cases the legacy `sqlite:///research_notebooks/bowaka_v2_lab/...` prefix so the path is honored as relative-to-lab-root rather than doubling up.
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::run_walkforward_study` wires the helper in so every storage URI used by an Optuna study is resolved before `OptunaStudy(storage_uri=...)`.
- `src/bowaka_v2_lab/reference/import_config.py` — generated configs now emit `sqlite:///artifacts/optuna/local.db` (resolved at runtime against the lab root) and a documentation comment for the PostgreSQL override path.

### 3.2 — Tests for path resolution
- `tests/integration/test_optuna_storage_path.py` — 7 tests: resolve relative path from lab CWD, resolve from repo root, legacy-prefix dedup, PostgreSQL passthrough, parent-dir creation, absolute-URI passthrough, unsupported-scheme raise.

### 3.3 — Stale defaults
- `src/bowaka_v2_lab/config/models.py::UniverseConfig` — `max_price` 1000.0 → 20.0 (live), `min_adv_dollars` 1_000_000 → 250_000.0 (live). Docstring documents the audit reference.
- `src/bowaka_v2_lab/config/defaults.py` — DELETED (audit-flagged as unused; the `DEFAULTS` dict has no importers anywhere in `src/`).
- `tests/unit/test_actual_mode_config_required_fields.py` — 9 tests: defaults match the live contract; shipped configs carry the live values; omitting universe fields falls back to live defaults; the deleted `defaults.py` import raises `ImportError`.

### 3.4 — Risk-control promotion gate (P1-004, user-selected option)
- `src/bowaka_v2_lab/optuna/promotion_gates.py` — new module with `HARD_RISK_CONTROL_FIELDS` (the six audited fields), `risk_control_drift(incumbent, candidate)` (returns the per-field drift list), and `evaluate_promotion(incumbent_params, candidate_params, requested_tier, feed)` (returns `{promotable, effective_tier, refusal_reasons, risk_policy_experiment, risk_drift, feed_cap_applied}`).
- `src/bowaka_v2_lab/optuna/walkforward_runner.py::run_walkforward_study` — after the existing promotion-evidence build, the gate runs over the best trial's params vs `_incumbent_baseline_params()` (or the per-trial incumbent when `incumbent_trial=True`). Any drift past epsilon labels `risk_policy_experiment: true` and caps the effective tier at `research_only`; the IEX feed cap runs in addition (independent). The capped tier overwrites the top-level `suitability_tier` AND is recorded in `promotion_evidence.json`.
- `tests/unit/optuna/test_risk_control_promotion_gate.py` — 14 tests: drift list correctness (identical, fractional, integer, eps, missing field, nested params), end-to-end promotion verdicts per (requested_tier, feed, drift) combination.

### 3.5 — Pytest mark hygiene (P2-002)
- `pyproject.toml::tool.pytest.ini_options.markers` — registered `optuna_smoke` and `paper_reconcile` markers (the prompt's segmentation hygiene). No existing tests are re-marked as `slow` in this phase to preserve the comprehensive-test default coverage; new selectors are available for future opt-in CI runs.

## Test results

| Group | Result |
|---|---|
| `tests/unit + tests/parity` | 796 passed (+22 vs Phase 2), 0 failed |
| `tests/integration + tests/reconcile` | 330 passed (+8 vs Phase 2), 12 deselected, 0 failed |
| `bowaka_common` | 97 passed (unchanged) |

## Verification of the §1.3 reproduction

The closing check (a tiny-lake walk-forward study under `allow_smoke=True`) is now passing with real (non-sentinel) `best_value`s instead of the pre-remediation `status=ok, best_value=-1e9` outcome — captured in the integration tests `test_walkforward_runner_invalid_study.py` and `test_walkforward_runner.py::test_run_walkforward_study_real_backtests`.
