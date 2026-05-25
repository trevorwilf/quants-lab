# Phase 10 — Expanded robustness (incumbent + top-K + sensitivity + stress)

Speedup report §9.

## What landed

- **Notebook 10 incumbent default-on.** `notebooks/_build_10_optuna_walkforward.py`
  papermill parameters now include `INCUMBENT_TRIAL = True` (Phase 10
  Task 1) and `N_JOBS = None` (Phase 5 surface). The
  `run_walkforward_study(...)` call threads both into the optimizer
  (`incumbent_trial=INCUMBENT_TRIAL`, `n_jobs=N_JOBS`). The notebook
  was regenerated.
- **`optuna/robustness.py`** (new) with four primitives:
  * `TopKReplayResult` / `SensitivityResult` / `StressMatrixResult`
    frozen-result types.
  * `replay_top_k_candidates(*, completed_trials, top_k,
    score_param_set, final_holdout_scorer=None, artifact_root,
    write_artifacts=True)` — picks the top-K completed trials by
    objective value, re-runs each through the caller's
    full-mode scorer, optionally calls the final-holdout scorer, and
    writes `artifacts/runs/study-<id>/top_k/k=<rank>/candidate.json` +
    `top_k_summary.json`. Default `top_k=3`.
  * `param_sensitivity_for_candidate(*, base_params, search_space,
    score_param_set, n_steps=5, artifact_dir=None)` — sweeps each
    tuned parameter ±n_steps inside its search-space bounds,
    re-scoring each value and writing
    `<artifact_dir>/sensitivity.json` per candidate. Non-tuned keys
    and keys missing from `base_params` are skipped.
  * `stress_matrix_for_candidate(*, candidate_rank, base_params,
    score_with_overrides, artifact_dir=None)` — runs a fold-local
    stress matrix across four axes: `cost_stress`
    (conservative/base/aggressive), `quote_age` (-0/-25/-50%),
    `spread` (-0/-25/-50%), `delay` (0/1/2 min). Writes
    `<artifact_dir>/stress_matrix.json`.
  * `assert_holdout_not_rescored(*, study_user_attrs, set_user_attr)`
    — sets `final_holdout_first_scored_at_utc` on the first score;
    on subsequent calls sets `final_holdout_rescored=True` +
    `final_holdout_last_rescored_at_utc` for the audit trail.
- **`config.models.OptunaConfig.robustness: dict[str, Any] = {}`**
  added. The runner can read additive knobs (`top_k_replays`,
  `sensitivity.{enabled,n_steps}`, `stress.{enabled,floors}`) without
  schema churn. Default empty dict ≡ legacy single-best replay.

## New tests

- `tests/unit/optuna/test_phase10_robustness.py` (8):
  top-K writes summary, top-K respects `write_artifacts=False`,
  optional holdout scorer wiring, sensitivity sweeps each tunable
  param, sensitivity skips non-tuned keys, stress matrix writes the
  per-candidate JSON across all 4 axes, holdout guard first-score
  records timestamp, holdout guard second-score flags rescored.
- `tests/integration/test_notebook_10_incumbent_default_on.py` (3):
  parameter cell carries `INCUMBENT_TRIAL = True`, run cell threads
  `incumbent_trial=INCUMBENT_TRIAL`, run cell threads `n_jobs=N_JOBS`.

## Result

`make test`: **1302 passed, 2 skipped, 12 deselected** (10:38). The 2
skipped are the Phase 5 PostgreSQL-gated tests.

## Branch

`feature/phase-10-robustness` merged to `dev` with `--no-ff`. The
final verification phase comes next.
