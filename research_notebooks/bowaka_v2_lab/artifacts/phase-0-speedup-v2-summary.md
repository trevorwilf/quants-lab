# Phase 0 — P0 correctness (startup-DQ + incumbent enqueue)

Speedup report v2 §1.1, §1.2, §4 P0-A and P0-B, §5.1, §5.2, §10.1, §11.1.

## What landed

- **`StartupDataQualityError(DataQualityError)`** in `data/data_quality.py`.
  A structural subclass — caught by the existing `except DataQualityError:`
  binding in `optuna.errors.structural_exceptions()`, so the Optuna runner's
  per-fold loop now propagates it instead of degrading to a sentinel score.
- **Backtester switches the abort point** (`sim/backtester.py:625`) from
  bare `RuntimeError(startup_dq_failure)` to
  `StartupDataQualityError(startup_dq_failure)`. The artifact write block at
  609–624 stays inside `if artifact_mode == "full":` so the failure manifest
  is still recorded.
- **Preflight `_check_data_quality` unified via `evaluate_startup_dq`**
  (`optuna/preflight.py`). The pre-remediation parity branch surfaced
  `adjustment_mismatch` / `split_adjustment_mismatch` as `warn`, silently
  allowing a study to run against a raw lake when the live contract requires
  adjusted daily bars. The unified path consults the same predicate the
  backtester uses, so adjustment-gating failures now mark the
  `data_quality` check as `fail` under `current_code_parity` (and continue
  to surface non-adjustment required failures as `warn`).
- **Runner short-circuit BEFORE `build_fold_contexts`**
  (`optuna/walkforward_runner.py`). `run_preflight(...)` is now invoked with
  `raise_on_fail=False`; on any failing check the runner synthesises a
  placeholder study name (via `build_study_name`), calls
  `_write_failed_study_artifact(...)` so the failed-status JSON lands at
  `paths.artifact_root/optuna/<study_name>.json`, and raises
  `OptunaStudyInvalidError`. The artifact write happens **before** any fold
  context is built (asserted by
  `test_walkforward_fails_before_context_build_on_raw_lake`).
- **Incumbent enqueue replaces dynamic-distribution pinning**. The legacy
  `_suggest_incumbent_params` (lines 921–993) is marked deprecated and its
  body now raises `NotImplementedError` so any stray import surfaces at
  call time. The replacement `_enqueue_incumbent_trial(study,
  incumbent_params, *, search_space_overrides=None) -> dict[str, dict]`:
  * Validates each name against the resolved search-space spec.
  * Clamps `uniform` / `log_uniform` / `int` into bounds; records the clamp.
  * **Refuses** silent clamping on `categorical` (raises
    `OptunaStudyInvalidError` so the operator widens / fixes the contract).
  * Refuses an incomplete incumbent (missing-key error).
  * Calls `study.enqueue_trial(checked_params,
    user_attrs={"incumbent_trial": True}, skip_if_exists=True)`.
- **Runner padding for contract gaps**. The frozen contract carries only a
  subset of every search-space key (`execution.max_quote_age_seconds` etc.
  are lab-only). The auto-path in `run_walkforward_study` pads any
  search-space key the contract omits with its search-space midpoint
  default and records the padded set on
  `study.user_attrs["incumbent_padded_from_search_space"]`, so the strict
  enqueue helper still succeeds while preserving the legacy "trial 0 is
  the incumbent for contract-covered keys" semantic.
- **Objective body simplified**. The `if incumbent_params and trial.number
  == 0:` special case (line 829–841) is removed; every trial calls
  `suggest_params(trial, overrides=search_space_overrides)` with the SAME
  resolved distributions. Trial 0's incumbent flag now arrives via the
  enqueue's `user_attrs={"incumbent_trial": True}` — `t.user_attrs.get(
  "incumbent_trial")` at lines 1881 / 2008 / 2014 continues to work.
- **Inline structural-propagation comment** added in
  `_run_validation_folds` (`except structural: raise` block) noting the new
  `StartupDataQualityError` chain — defence-in-depth so a future reader
  does not weaken the propagation by mistake.

## New tests

- `tests/unit/data/test_startup_data_quality_error_subclass.py` (4):
  isinstance chain, structural-tuple match, catch-by-parent, legacy
  `RuntimeError` back-compat.
- `tests/unit/optuna/test_preflight_fails_current_code_adjustment_gating.py`
  (5): adjustment-gating fails closed in parity AND realism; non-adjustment
  required failures still warn in parity; smoke-allow path stays
  passing/skipped; clean report passes.
- `tests/unit/sim/test_startup_dq_raises_structural.py` (2): the
  backtester raises `StartupDataQualityError` when the gate fires; the
  exception is catchable as `DataQualityError`.
- `tests/integration/test_run_validation_folds_propagates_startup_dq.py`
  (2): both `objective_minimal` and `full` artifact paths re-raise
  `StartupDataQualityError` instead of degrading.
- `tests/integration/test_walkforward_fails_before_context_build_on_raw_lake.py`
  (1): end-to-end raw-IEX-lake parity config terminates with
  `OptunaStudyInvalidError` BEFORE `build_fold_contexts` is called; the
  failed-status artifact contains `adjustment_mismatch` in
  `failure_reason`.
- `tests/unit/optuna/test_incumbent_enqueue_stable_search_space.py` (1):
  3 trials of an enqueued incumbent show no FAIL state, no Optuna
  "dynamic value space" warnings, trial 0 records the incumbent value +
  `incumbent_trial=True` user attr, trials 1+ sample freely.
- `tests/unit/optuna/test_incumbent_out_of_bounds_behaviour.py` (4):
  float-below-bound clamps; categorical-not-in-choices refuses (no
  enqueue call); missing-required-key refuses; in-bounds incumbent
  records no clamps.

## Existing tests touched

- `tests/integration/test_optuna_refuses_current_code_parity_without_flag.py`
  — `_write_parity_cfg` now disables `require_adjusted_daily_bars` /
  `require_split_adjustment` for its tiny synthetic lake (which carries
  no adjustment manifest). The test's purpose is the parity-gate admission
  flow, not the DQ adjustment-gating refusal; the docstring documents
  the change. Production parity studies against a real lake continue to
  require adjustment, and the new Phase 0 gate refuses them when the lake
  is raw (asserted by the new
  `test_walkforward_fails_before_context_build_on_raw_lake`).

## Tests

| Gate | Result | Time |
|---|---|---|
| `make test-fast` (unit + parity) | **958 passed**, 0 failed | 40.6s |
| `make test-integration` (timeout=300) | **320 passed**, 2 skipped (PG-gated), 12 deselected (live) | 13:45 |

## Acceptance

- The current `bowaka_v2_actual_iex_current_code_optuna.yml` on a raw IEX
  lake terminates with `OptunaStudyInvalidError` BEFORE
  `build_fold_contexts(...)` is called (proved by
  `test_walkforward_fails_before_context_build_on_raw_lake`).
- The deprecated `_suggest_incumbent_params(...)` raises
  `NotImplementedError` if anything calls it.
- No existing test changes its assertions on the startup-DQ degraded-fold
  path. The parity-admission test changes its fixture config (documented).

## Branch

`feature/phase-0-optuna-correctness` — merged to `dev` with `--no-ff`.
