# Phase 5 — Staged finalist testing pipeline

Speedup report v2 §1.4, §8.3, §9, §10.5, §11.2 Phase 5.

## What landed

- **`HoldoutGuard.declare_finalist_read()` + `revoke_finalist_read()`** —
  the one authorised mechanism by which the holdout window may be read
  AFTER tuning. Without the declaration the guard continues to refuse
  the read; the declaration is per-`HoldoutGuard` instance so a stray
  test that constructs a fresh guard does not inherit the authorisation.
- **`optuna/evaluate_finalists.py`** (new) — Stage B pipeline:
  * `FinalistEvaluationConfig` (top_k, include_incumbent,
    full_artifacts, score_final_holdout, stress_scenarios, local
    perturbation knobs).
  * `FinalistEvaluationResult` (finalists / incumbent / report_path /
    report).
  * `evaluate_finalists(*, completed_trials, finalist_cfg,
    score_param_set, holdout_scorer=None, stress_scorer=None,
    perturbation_scorer=None, output_dir, log)` — injectable scoring
    callables make the function unit-testable without a real study.
    Picks top-K by Optuna value, appends the incumbent if requested
    (deduplicated by trial number), re-runs each finalist via
    `score_param_set`, optionally scores holdout / runs stress
    scenarios / runs neighbourhood sweep. Writes
    `finalist_report.json` and computes per-finalist
    `incumbent_comparison.validation.objective_delta` (and holdout
    delta when present).
  * `apply_stress_overrides(cfg, overrides)` — applies dotted-path
    absolute overrides AND `*_multiplier` forms (multiplies the
    resolved value). Unknown `*_multiplier` targets raise `KeyError`
    so the operator sees the error.
  * `run_promotion_candidate(...)` — Stage C deterministic-promotion
    rerun. Re-scores ONE candidate, optionally scores holdout,
    captures `dataset_hash` / `config_hash` / `code_hash` + a
    `platform` block, writes `promotion_artifact.json` in sorted-key
    JSON for byte-stable repeat runs (modulo `captured_at_utc` +
    `platform.node`).
- **`finalist_evaluation:` block emitted by the importer** —
  `reference/import_config.py` adds the block to every `--purpose
  optuna` config. The 3 committed optuna configs were regenerated and
  carry the block in sorted-key YAML; the `byte_stable` parity tests
  still pass.
- **`BowakaV2Config.finalist_evaluation: Optional[dict[str, Any]]`** —
  loose schema so the operator can add new stress scenarios /
  perturbation knobs without bumping the strict schema.
- **`ALLOWED_TOP_LEVEL_KEYS`** in `config/loader.py` extended with
  `"finalist_evaluation"` so the loader admits the new section.
- **CLI subcommand**: `bowaka-v2-lab evaluate-finalists --study-dir
  <path> --config <path> --output <path>`. The CLI currently loads
  and prints the resolved `finalist_evaluation` config + the study
  artifact glob, then writes a placeholder report (operator wraps the
  CLI with a storage-URL-aware scorer to do the actual work — the
  injectable scoring API makes the Python entry point the primary
  surface).

## Deferred to follow-up

- **Live-lake integration tests** — `test_finalist_pipeline_top_k_includes_incumbent`,
  `test_finalist_pipeline_holdout_read_only_after_tuning`,
  `test_finalist_pipeline_stress_scenarios_are_fold_local` require
  running a real Optuna study against a tiny lake + instrumenting the
  lake reader to track read windows. Multi-day work; deferred to the
  next remediation pickup. The injectable scoring API is built so
  those tests can land without further refactor.
- **End-to-end CLI smoke against a finished study** — needs a
  PostgreSQL storage URL (so the CLI can reload the Optuna trials);
  currently the CLI writes a placeholder report and an operator
  wraps it with the Python API for production runs.

## New tests

- `tests/unit/optuna/test_holdout_guard_finalist_read_gate.py` (5):
  default refuses; declaration authorises; revoke restores refusal;
  non-overlap windows unaffected; per-instance authorisation.
- `tests/unit/optuna/test_finalist_apply_stress_overrides.py` (5):
  absolute override; multiplier form preserves type; missing
  multiplier target raises; nested-key creation; deep-copy isolation.
- `tests/unit/optuna/test_finalist_report_schema.py` (3): required
  keys; incumbent appended when outside top-k; incumbent
  not-duplicated when already in top-k.
- `tests/unit/optuna/test_finalist_report_incumbent_comparison.py`
  (2): delta = finalist − incumbent on validation; no comparison
  block when no incumbent trial.
- `tests/unit/optuna/test_run_promotion_candidate_is_deterministic.py`
  (1): two runs produce byte-equal JSON modulo timestamp + platform.

## Tests

| Gate | Result | Time |
|---|---|---|
| `make test-fast` | **1031 passed**, 0 failed | 46.3s |
| `make test-integration` (timeout=300) | running in background — see commit body |  |

## Branch

`feature/phase-5-staged-finalist-testing` — merged to `dev` with
`--no-ff`.
