I have everything I need. Let me do one final check on the `n_active_days` source in the summary and whether the daily drawdown could exceed 1.0 (since bankroll can't go negative typically, drawdown caps at ~1.0; but `_LOSS_DECIMAL_MAX=1.5` so safe). Let me also confirm the `_resolve_symbols` `available_symbols` call in the non-IR lake branch could be unbounded — actually it's capped `[:cap]`. 

Let me verify one subtle lead: the `mark_to_market_drawdown` peak starts at `series[0]` not as a running max from the actual initial bankroll, and uses `if peak > 0` — confirmed fine. And the worst-day-loss uses raw daily bankroll which already includes intraday. 

I now have a complete, thorough picture. Let me write the report.

## Purpose & data flow (how this subsystem fits the backtest pipeline)

`optuna_core` is the Bayesian-optimization heart of bowaka_v2. `run_walkforward_study` (walkforward_runner.py:1848) is the entrypoint: it loads a config, runs admissibility/parity/preflight gates, builds a walk-forward `plan` (`build_walkforward_splits`, walkforward.py:47), precomputes one immutable `FoldRuntimeContext` per validation split (fold_context.py), then drives Optuna. Each trial samples params from `SEARCH_SPACE_SPEC` (search_space.py:62), derives gap/ratio→strategy fields (`apply_trial_params`, :428), runs a real `run_backtest` over every validation window, converts each to a `FoldResult` (objective.py), and scores the trial as `median(fold_scores) - fold_variance_penalty` (`compute_objective`, objective.py:667). The final-holdout window is reserved at the tail and guarded (holdout_guard.py) — never read during tuning. Output: a results JSON + `promotion_evidence.json` + phase-profile JSON. Parallel execution rebuilds contexts per-worker via the dotted factory `make_walkforward_objective_for_worker` (:942).

## Behavioral spec

- **Fold construction** (walkforward.py:47-81): rolling `train_months`/`val_months` (defaults 6/1), `step_months = step_months or val_months` → folds overlap by `train_months - val_months`. `final_holdout` carved from tail (`_add_months(full_end, -final_holdout_months)`). Loop breaks when `val_end > final_start`.
- **NO embargo/purge gap** between train and validate: `val_start = train_end` exactly (walkforward.py:75). Adjacent train/val are contiguous; no decorrelation buffer.
- **Half-open `[start,end)` sessions** (calendar_sessions.py:22): end date excluded by stepping `closed_end = end - 1 day`; `val_end == final_holdout_start` does NOT leak the holdout's first session.
- **Holdout guard** (holdout_guard.py:58): raises unless `end <= holdout_start or start >= holdout_end`, or `_phase=="final_eval"`, or `_finalist_read_declared`. Asserted per fold (walkforward_runner.py:806).
- **Objective formula** (objective.py:659-732): `fold_score = net_return - sum(penalties)`; penalties = drawdown(0.5×MTM-DD) + cvar(0.5×worst-day) + turnover(1.0) + concentration(1.0) + low_trade_count + missing_quote(0.02×count) + missing_coverage(1.0×shortfall) + fill_rate(0.5×shortfall) + pick_quality(0.10×frac-below-0.5%). Trial objective = `median - 0.5×stdev(fold_scores)`.
- **Why scores go negative on positive PnL**: `net_return` is the median FOLD return (decimal), but penalties are absolute decimals that can sum > the median return — e.g. coverage shortfall (up to 1.0), turnover (unbounded ×1.0), fill-rate shortfall (0.5). A +15% PnL fold (`net_return=0.15`) with 60% coverage loses `1.0×0.40=0.40` alone → strongly negative (matches MEMORY note).
- **Drawdown uses DAILY mark-to-market** bankroll (`mark_to_market_drawdown`, objective.py:329), NOT closed-trade `max_drawdown_pct`. Peak seeded at `series[0]`, guarded `if peak>0`.
- **Units guard** (objective.py:78-171): `MetricUnits` rejects `|net_return|>2.0`, DD/loss>1.5, coverage/fill>1.5; `compute_objective` validates every fold unless `validate_units=False`.
- **Incumbent trial-0** (walkforward_runner.py:1305 `_enqueue_incumbent_trial`): enqueued via `study.enqueue_trial` (NOT distribution collapse — old `_suggest_incumbent_params` is a `NotImplementedError` stub, :1278). Values clamped into bounds for numeric; categorical out-of-range RAISES.
- **gap/ratio derivation** (`_derived_strategy_fields`, :386): `hard=min(0.70, soft+hard_gap)`, `critical=min(0.90, hard+critical_gap)`, `target_pct=min(0.40, stop_pct×ratio)`. Idempotent (`_derive_strategy_params`, :410).
- **Pruning** (walkforward_runner.py:1168, default OFF): after each fold, if `n_complete >= min_completed_before_prune` (30) and `running_score <= catastrophic_floor` (-0.5), raise `TrialPruned`. Pruned trials excluded from best selection (:2695).
- **Degraded fold** (`_degraded_fold`, :748): worst-possible sentinel (`net_return=-1, DD=1, fill=0, fold_status="degraded"`) on any non-structural exception; any degraded fold invalidates the trial (:2728).
- **Validity gates** (:2746 `evaluate_study_validity` + :2707 per-trial): reject sentinel scores, missing fold metrics (`len != n_splits`), degraded folds, plus `CONSTANT_OBJECTIVE_SURFACE`/`NO_TRADE_STUDY`/`INCUMBENT_MAPPING_INCOMPLETE`. Zero valid → failed artifact + raise.
- **Caching layers**: `FoldRuntimeContext` caches sessions/scan_times/PIT-universe/daily-cache/suppliers (trial-invariant); `startup_dq_cache` (invariant DQ half); `scan_matrix_store`; `batch_daily_cache`; `session_minute_window_cache`; LRU `cached_suppliers`. All keyed/guarded.

## Knobs (config fields)

- `optuna.walkforward.{train_months=6, val_months=1, final_holdout_months=1}` → plan windows (:1933). No `step_months` config wiring — always defaults to `val_months`.
- `optuna.n_trials=20, n_jobs=1, n_startup_trials=10` (:2187); `run.seed=1337` but sampler seed is hard-coded `1337` (:2641, see Leads).
- `optuna.objective_artifact_mode` ("full"|"objective_minimal", :2477) → minimal skips disk artifacts, reads in-memory result.
- `optuna.search_space_overrides` (:1928) → per-key `(kind,...)` or `"freeze"` (`resolve_search_space`, search_space.py:162).
- `optuna.pruning.{enabled=False, min_completed_trials_before_pruning=30, catastrophic_floor=-0.5}` (:1142).
- `optuna.cached_suppliers=False` (:2499); `optuna.acceleration.{startup_dq_cache,batch_daily_cache,session_minute_window_cache,scan_matrix}.enabled` (fold_context.py:288,319,349; :179).
- `optuna.parallel.{strict_parallel=False, memory_reserve_gib=32, max_workers=8}` (:2501).
- `optuna.preflight.research_waiver_capped_symbols=False` (:1963) → bypasses IR full-PIT-union coverage gate.
- `optuna.debug_first_n_trials=3`, `debug_trials_force=[]` (:1155).
- `simulation.mode` (smoke_fixture|current_code_parity|intended_realism|fast_realism) gates admissibility (:201,238).
- `market_data.require_adjusted_daily_bars` required True for IR (:269). `execution.max_quote_age_seconds` default 60 (:527).
- `PenaltyWeights` (objective.py:200) are code constants, NOT config — surfaced in metadata but not tunable per-run (`gap_through_stop`/`same_minute_ambiguity` default 0.0).

## Invariants & guards

- **Fail-loud**: undeclared contract divergence → `OptunaParityError` (:153); `current_code_parity` study without opt-in → `CurrentCodeParityStudyRefused` (:201); IR data insufficient → `IntendedRealismDataInsufficient` (:238); preflight fail → failed artifact + `OptunaStudyInvalidError` (:2155); context-affecting search key → `OptunaStudyInvalidError` (fold_context.py:130); scan-matrix configured-but-unopenable → raises (fold_context.py:202); incumbent categorical out-of-bounds → raises (:1359); incumbent missing key → `INCUMBENT_MAPPING_INCOMPLETE` (:1467); search-space version mismatch on study reuse → raises (:1478); structural exceptions propagate (errors.py:79).
- **Silent fallbacks (flagged)**:
  - **`_run_fold_backtest` corrupt report.json → `summary["_report"]={}`** (:604), then `_fold_result` uses closed-trade `max_drawdown_pct` fallback instead of daily MTM (:733) — silently swaps the drawdown source the audit requires.
  - **`startup_dq_cache` build failure → `startup_dq_report=None`** swallowed (fold_context.py:442) — degrades to per-trial rebuild silently (perf only, but masks a real DQ-cache defect).
  - **`_resolve_symbols` IR empty PIT-union → falls back to all lake symbols** (:362) silently; relies on downstream DQ to surface.
  - **content-addressed dataset hash failure → logical hash** (:2228), warn-only — lineage silently weakens.
  - **PIT-union coverage telemetry failure → coverage "unknown"** (:1980), and the IR coverage gate at :1983 only fires when `preflight_coverage_fraction is not None`, so a telemetry exception silently bypasses the full-union coverage refusal.
  - **manifest daily_adjustment unreadable → silently uses effective** (:2358).
  - **best-trial report exception → `{"error":...}`** swallowed (:2918), study still emits "ok".

## Leads (suspected bugs / realism gaps / smells)

- walkforward.py:75 — **no embargo/purge gap**: `val_start == train_end`; adjacent overlap of train/val baselines (prior-day ATR/EMA carry into val day 1). Standard WF leakage concern; not addressed anywhere.
- walkforward.py:65 — `step_months` parameter exists but is **never wired from config** (only `train/val/final_holdout_months` are read at :1933); folds always step by `val_months`, so train windows overlap heavily and folds are highly correlated (inflates apparent stability, deflates `fold_variance`).
- walkforward_runner.py:2641,2389 — **sampler seed hard-coded `1337`** ignoring `run.seed` (read at :2192 but only stored in metadata). A study cannot be re-seeded for multi-seed robustness via config.
- objective.py:419,491,529 / metrics.py:87 — **`net_return_pct` misnomer**: the field is a DECIMAL (`(final-init)/init`), not percent, yet named `_pct`. Correct numerically but a documented trap; one future `×100` "fix" silently trips MetricUnitsError or 100×-inflates the objective.
- objective.py:627 — **`turnover` penalty weight 1.0 with no upper clamp**: `turnover` can be >1 (multiple round-trips), making one term dominate `net_return`. Unbounded penalty vs bounded coverage/fill terms.
- objective.py:702-704 — penalty breakdown aggregated as **mean across folds while objective uses median** fold score; `objective_terms` decomposition is explicitly only "≈" (admitted :716) — a reviewer reconciling terms to objective will see mismatch.
- walkforward_runner.py:733-745 — **degraded/empty-window fallback uses closed-trade `max_drawdown_pct`** and `worst_day_loss=0.0`, contradicting the "daily MTM only" contract; an empty-session fold gets `worst_day_loss=0` (penalty-free) which is optimistic.
- walkforward_runner.py:1715 `_neighbour_param_sets` — neighbours perturb `best.params` which still hold gap/ratio keys; categorical neighbours use `rng.choice` (can equal original → "neighbour" == point); `int` step `rng.choice([-1,0,1])` can yield 0 → identical neighbour. Robustness sweep may silently re-score the same point.
- fold_context.py:323 — `session_minute_window_cache` only applies when **`cached_suppliers` also True** (AND gate); enabling the flag alone is a silent no-op (no warning).
- fold_context.py:144 — `CONTEXT_AFFECTING_PREFIXES` guard matches by prefix; a search key like `marketing.x` would false-match `market_data.`? No — it checks `name.startswith("market_data.")`. But `session.scanner_start` is matched by equality only; a key `session.scanner_startup` would NOT be caught though it could affect scan cadence. Edge smell.
- walkforward_runner.py:1413 — `_incumbent_gap_ratio_from_config` only emits `reward_risk_ratio` when `stop_pct not in (None,0,0.0)`; a config with `stop_pct=0` silently drops the ratio key → `INCUMBENT_MAPPING_INCOMPLETE` raise later, opaque cause.
- search_space.py:90 — comment "live 0.01 frac = 100 bps" but bound is `("int",5,200)` and live is annotated 100 bps; verify the live `max_spread_bps` actually equals 100 and is covered — search lower bound 5 bps may be far tighter than live; the coverage test should catch but worth checking.
- objective.py:135-149 — **MetricUnitsError on DD>1.5**: a leveraged/shorting fold whose daily bankroll briefly prints a >150% drawdown (or a coverage row >1.5 from a metric bug) crashes a whole VALID trial via `compute_objective` (called in `prune_callback` too, :846 — though there it's caught). In the main path (:1207) a MetricUnitsError is non-structural → degrades the whole trial to sentinel. Fragile.
- walkforward_runner.py:1983 — IR coverage gate is **bypassed when telemetry raised** (`preflight_coverage_fraction is None`); combined with the `except Exception` at :1980 this is a silent escape hatch from the full-PIT-union requirement.
- fold_context.py:331 — `make_session_minute_window_supplier(..., max_bar_age_seconds=None)` hard-coded "legacy parity"; if config sets a bar-age, it's ignored on this path (realism gap when the cache is enabled).
- walkforward_runner.py:540,553 — `scan_times_callable` lambdas capture loop-free vars; fine, but the no-ctx path rebuilds suppliers per fold while ctx path reuses — two code paths claimed "semantically identical, only slower" but only proven by parity tests, not asserted at runtime.
- objective.py:696 — `fold_variance = stdev` requires `len>1`; a **single-fold plan → zero variance penalty**, so a 1-fold study's objective == its single fold score with no stability discount (over-trusts a 1-fold result). No minimum-fold gate.

## Test coverage hooks

- **search_space**: `test_search_space_versioned.py`, `test_search_space_covers_actual_values.py`, `test_search_space_relation_constraints.py`, `test_stop_pct_in_search_space.py`, `test_search_space_version_bumped_to_3.py`, `test_optuna_search_space_priors.py`.
- **objective**: `test_objective_units_consistent.py`, `test_optuna_objective_penalties.py`, `test_objective_low_trade_penalty.py`, `test_objective_uses_mark_to_market_drawdown.py`, `test_fold_result_from_backtest_result.py`, `test_gap_through_stop_penalty.py`, `test_same_minute_ambiguity_penalty.py`, `test_fold_activity_gates.py`, `test_objective_minimal_parity.py`, `test_objective_term_breakdown_in_user_attrs.py`.
- **fold construction / holdout**: `test_walkforward_splits.py`, `test_xnys_sessions_half_open.py`, `test_walkforward_final_holdout_excluded.py`, `test_walkforward_no_holdout_session_read_at_boundary.py`, `test_holdout_guard_boundaries.py`, `test_final_holdout_not_accessible_during_trial_objective.py`.
- **incumbent / pruning / validity**: `test_incumbent_*` (4), `test_pruning_*` (3+`test_pruned_trials_excluded_from_promotion`), `test_study_validity_*` (4), `test_walkforward_rejects_degraded_folds_in_valid_trial_filter.py`.
- **caches**: `test_fold_context_*` (parity/batch/no-mutation/invariants), `test_cached_*`, `test_scan_matrix_*` (extensive parity), `test_run_validation_folds_propagates_startup_dq.py`, `test_cached_startup_dq_does_not_change_objective.py`.
- **NO direct test found for**: `step_months` config wiring (parameter is dead, untested by config path); the **`run.seed` → sampler-seed** disconnect (sampler seed hard-coded — no test asserts config seed reaches the sampler); `_neighbour_param_sets` producing identical-to-point neighbours (no degeneracy test); the **corrupt-report.json → closed-trade-DD fallback** branch (:604/:733 — no test exercises a corrupt report swapping the drawdown source); single-fold zero-variance behavior; the IR coverage-gate telemetry-exception bypass (:1980→:1983).