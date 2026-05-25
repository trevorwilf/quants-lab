# Phase 7 — Conservative Optuna pruning (default off)

Speedup report §6.2 / §11.2.

## What landed

- **`config.models.OptunaConfig.pruning: dict[str, Any] = {}`** —
  free-form dict so the runner can read additive knobs without
  schema churn. Recognised keys:
  * `enabled: bool` (default `False`)
  * `min_completed_trials_before_pruning: int` (default `30`)
  * `catastrophic_floor: float` (default `-0.5`)
  * `use_running_median_after_warmup: bool` (reserved)
  * `allow_pruned_in_promotion: bool` (reserved)
- **`_run_validation_folds(..., prune_callback: Optional[Callable[[int,
  float], None]] = None)`** — new optional hook called once after each
  completed fold with `(fold_index, running_score)`. The callback may
  raise `optuna.TrialPruned` to abort the trial early; default `None`
  preserves the legacy no-prune flow.
- **`make_walkforward_objective` pruning wiring:**
  reads `cfg.optuna.pruning`; when `enabled=true` AND
  `len(study.completed) >= min_completed_trials_before_pruning` AND
  `running_score <= catastrophic_floor`, calls `trial.report` for the
  visualiser and raises `optuna.TrialPruned`. The objective explicitly
  re-raises `TrialPruned` from the broad-except so Optuna records the
  trial as PRUNED (not COMPLETED, not FAILED).
- **`run_walkforward_study` post-optimize:** counts pruned trials and
  records `n_pruned_trials` on the study's user_attrs. The existing
  `optuna.trial.TrialState.COMPLETE` filter naturally excludes pruned
  trials from the best-trial pool.

## New tests

- `tests/unit/optuna/test_pruning_default_off.py` (2).
- `tests/integration/test_pruning_catastrophic_floor.py` (5):
  catastrophic-trial pruned, good-trial completes, startup window
  respected, pruning fires once past the startup window, user_attrs
  recorded on prune.
- `tests/integration/test_pruned_trials_excluded_from_promotion.py` (2).
- `tests/integration/test_no_pruning_parity_with_baseline.py` (1):
  omitting the pruning block produces byte-identical results to
  `enabled: false`.

## Result

`make test`: **1248 passed, 2 skipped, 12 deselected** (10:26). The 2
skipped are the Phase 5 PostgreSQL-gated tests.

## Branch

`feature/phase-7-conservative-pruning` merged to `dev` with `--no-ff`.
Phase 8 takes off from `dev` next.
