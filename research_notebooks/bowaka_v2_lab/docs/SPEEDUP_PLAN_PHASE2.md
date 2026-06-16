# Phase-2 Finalist Sweep — Efficiency & Speedup Plan

*Produced 2026-06-16 by a comprehensive parity-aware investigation (12-surface discovery →
dedup → adversarial verify → synthesize; 28 agents, 47 raw findings → 14 candidates → 7
confirmed). Sibling to `docs/SPEEDUP_PLAN.md` (phase-1 search). Scope: the post-search
finalist vetting in `scripts/topn_robustness_sweep.py`, invoked as a subprocess by
notebook 10. Goal: parity-safe (byte-identical objective/holdout-score) wins specific to
this path. "Adjusted impact" = the realistic figure after adversarial scrutiny.*

> **Baseline context.** The phase-2 backtests already inherit every shipped backtester win —
> `c1` (DQ/IO caches), `c5` (gate manifest), `c18`/`c19` (scan-matrix memo/score-mask),
> `c30`/`c31` (loop-invariant hoist + event-log gate), `c29` (`lru_cache` max_hold) — and the
> 47x scan-matrix lever is engaged on **both** phase-2 backtest paths (validation + holdout)
> (`separate_holdout_matrix: false` ⇒ holdout opens a real store ⇒ matrix-fast, not legacy).
> So the heavy per-backtest machinery is already optimized. The remaining wins are (a) one
> true parallelism fix and (b) a set of small invariant-hoist / dead-work removals.
> **There is no second 47x hiding on this path.**

---

## 1. Headline

**The single biggest phase-2 lever is `p2-pin-blas-threads-workers`: pin the 6 BLAS thread
env vars to `1` in the parent before the fork pool is built.**

The 5000-trial search path already pins BLAS to 1 in every worker (`optuna/parallel.py`,
before numpy import). The phase-2 sweep does **not** — it forks up to `cpu-2` workers
(`topn_robustness_sweep.py:806,809-811`), each inheriting `os.environ` unmodified and each
spinning a default (~`cpu`-wide) BLAS threadpool inside `run_backtest`. On the 18-core box
that is ~16 workers × ~16 BLAS threads contending for cores the worker pool already
saturates. Because the pool already fills every core, the cost is cache-thrash /
context-switch / lock contention (not the idle-box catastrophe), so the realistic recovery
is **~3–12% of sweep wall-time** — but it is trivial, zero-risk, multiplicative across every
`top_n × (neighbours × folds + 1)` backtest, and it makes the sweep numerics **match** the
already-pinned search path rather than diverge.

It must be set **in the parent before the executor block** — under `fork`, numpy/BLAS
threadpools are already initialized in the parent at fork time, so pinning inside
`_eval_finalist` is too late (the search path can pin per-worker only because it uses `spawn`).

---

## 2. Parity-safe wins (largest-first)

| # | ID | Site | Adjusted impact (honest) | Effort |
|---|----|------|--------------------------|--------|
| 1 | `p2-pin-blas-threads-workers` | `topn_robustness_sweep.py:809`; helper `optuna/parallel.py:68-75` `pin_blas_threads_to_one` | **~3–12% sweep wall-time** (kills O(cpu²) thread oversubscription); multiplicative across every backtest. Highest-leverage. | trivial |
| 2 | `p2-finalist-neighbour-task-granularity` | `topn_robustness_sweep.py:812` (one future/finalist) → `64×7` neighbour futures + 64 holdout futures | **Tail-only ~2–6%** typical, up to ~10% on unlucky last-wave / small `top_n`. | medium |
| 3 | `p2-reuse-eligible-per-session` | `walkforward_runner.py:716-718` (hot in phase-2) + `:591-593` | **<1%**; drops ~21 `sorted()`+filter passes/backtest; ctx already froze the value. | trivial |
| 4 | `p2-hoist-auctions-supplier` | `walkforward_runner.py:681` (+`:555`); `FoldSupplierBundle` `fold_context.py:71-81`, build at `:468` | **~0.1s SSD / negligible**; seconds only on a 9p mount (prod is off-9p). Removes ~1,408 redundant `MarketDataStore` ctor + `exists()`. | low |
| 5 | `p2-load-study-no-deepcopy` | `topn_robustness_sweep.py:756` → `get_trials(deepcopy=False, states=(COMPLETE,))`; `:728` → `get_trials(deepcopy=False)` | **~0.5–3s one-time startup**; avoids deep-copying ~5000 FrozenTrials. | trivial |
| 6 | `p2-compute-objective-single-penalty-pass` | `optuna/objective.py:694` + `:700-704` (`fold_penalties` runs 2×/fold) | **sub-second** phase-2; also benefits the search path (larger absolute win there). | trivial |
| 7 | `p2-standalone-best-report-ctx-reuse` | `walkforward_runner.py:2598` (`fold_contexts=None`) → build once, pass to `:2935` | **Standalone/CLI path only** (notebook passes `skip_best_trial_report=True`). Parity is config-dependent — see §4. | low |
| 8 | `p2-skip-discarded-objective-terms` | `optuna/objective.py:699-723` (additive `terms=False` kwarg) | **Negligible standalone**; only worth it *bundled with #6*. | low |

---

## 3. Compounding estimate

Items are largely independent and stack (multiplicative):
- **#1 BLAS pin:** ~3–12% → ~0.88–0.97
- **#2 task granularity:** ~2–6% → ~0.94–0.98
- **#3 + #4 + #6:** combined <1–2% → ~0.98–0.99
- **#5 deepcopy:** one-time ~0.5–3s → ~0%

**Combined realistic phase-2 speedup ≈ 6–18% wall-time**, dominated by #1 with #2 second.
This is a "many small things" plan, not a second 47x — the matrix lever (already engaged)
was the last big multiplier on this path. Be skeptical of figures near the top of these
ranges: #1 and #2 are *contention/tail* wins that depend on box size and finalist count, and
at the script default `--top-n 12` (one wave on 16 workers) #2 collapses to just the
single-holdout-straggler reduction.

> **Absolute-time caveat (operator note):** the synthesis quoted a "~21h sweep" baseline,
> which is the *pre-c1/pre-matrix* figure. Post-optimization (c1 + the 47x matrix engaged on
> both paths) a 64-finalist sweep is far shorter — on the order of the ~70-min parent
> context build + ~1–1.5h of fork-parallel backtests. So 6–18% is **tens of minutes**, not
> hours. Treat the percentages as the reliable signal.

---

## 4. Recommended implementation order (grouped by risk)

### Group A — zero-risk, trivial, byte-identical (ship first)
1. **#1 `p2-pin-blas-threads-workers`** — call `pin_blas_threads_to_one()` in the **parent**
   immediately before the executor block (`topn_robustness_sweep.py:809`). Highest payoff
   for least effort. Care: parent, not worker (fork timing).
2. **#5 `p2-load-study-no-deepcopy`** — `:756` → `get_trials(deepcopy=False, states=(COMPLETE,))`;
   `:728` → `get_trials(deepcopy=False)`.
3. **#3 `p2-reuse-eligible-per-session`** — `walkforward_runner.py:716-718` (+`:591-593`) →
   `{s: set(ctx.eligible_symbols_by_session[s]) for s in sessions}` (ctx branch only; keep
   the no-ctx legacy recompute). (This is the phase-1 c21 candidate — *worth it here* because
   it is hot in the per-finalist sweep, unlike the search path where it was marginal.)

All three touch no matrix-hash file and have no plumbing risk.

### Group B — small structural edits, verify parity (second PR)
4. **#6 `p2-compute-objective-single-penalty-pass`** — compute `fold_penalties(f)` once per
   fold; reuse the dict (preserve the `float()` wrap). Run the objective-term-breakdown tests.
5. **#8 `p2-skip-discarded-objective-terms`** — bundle with #6; additive `terms=False`
   (default **True** — search path + `test_objective_term_breakdown_in_user_attrs.py` consume
   the breakdown).
6. **#4 `p2-hoist-auctions-supplier`** — defaulted `auctions` field on `FoldSupplierBundle`;
   build once at `:468`; read `ctx.suppliers.auctions`. Keep inline on the no-ctx branches.

### Group C — medium / conditional, do last with explicit verification
7. **#2 `p2-finalist-neighbour-task-granularity`** — three correctness requirements the raw
   candidate under-stated: (a) generate all 7 neighbours in the parent with `n_neighbours=7`
   (the `random.Random(20260521)` state advances across index *and* params — per-sub-task
   `n_neighbours=1` would change the numbers); (b) order-preserving regroup (`neighbour_scores`
   is an ordered list in the report + JSON); (c) per-sub-task error mapping (neighbour→`None`,
   holdout→`holdout_error`) and per-task `HoldoutGuard`.
8. **#7 `p2-standalone-best-report-ctx-reuse`** — only in the `not skip_best_trial_report`
   branch. **NOT byte-identical universally:** for `runtime_mode=disabled` it is identical;
   for vectorized-matrix configs the current no-ctx path passes `scan_matrix_store=None` →
   raises → neighbour scored `_FAILED_TRIAL_SCORE`, while with-ctx opens the real store and
   produces a *real* score (degraded→real, i.e. a **bug fix**, not parity). Complementary to
   the shipped `--skip-best-trial-report` flag; only helps a standalone study run *without* it.

---

## 5. Do NOT pursue

| ID | Why |
|----|-----|
| `p2-asset-master-memo` | **Matrix-hash violation** — `universe/builder.py` is in `_MATRIX_HASH_SOURCE_FILES`; the cache changes the file bytes → invalidates the built matrix → forces a full rebuild ≫ the few-seconds saving. (Revivable only if relocated out of the 5 hash files, e.g. onto `MarketDataStore.assets`.) |
| `p2-hoist-classify-instrument` | **Matrix-hash violation + overstated.** Same hash file. The classify collapse is one-time parent CPU (<1% of the ~70-min build), not multiplied by finalists. Candidate's `snapshot_id` cache key is also unsafe (can be `None`). |
| `p2-batch-daily-reuse-pit-history` | **Matrix-hash violation + high-effort + parity-fragile.** Extends `_CachedDailyHistory` (a hash-source class); the 400-day EMA truncation is load-bearing (`test_batch_daily_cache_truncated_ema_parity.py`). |
| `p2-drop-defensive-dict-copies` | **Real but unmeasurable** — removes 2 shallow ~21-entry `dict()` copies/backtest; sub-second cumulative. Fold into a larger cleanup only if convenient. |
| `p2-latent-evaluate-finalists-parallel-and-minimal` | **Zero impact — dead code.** `evaluate_finalists()` has no production caller (the CLI is a skip-stub); the real path already has fork + `objective_minimal` + deepcopy. |
| `p2-nonfinding-holdout-matrix-deepcopy` | **Verified non-finding (0x).** The `walkforward_runner.py:484` deepcopy is in the `store is None` branch, guarded by the `:479` early-return; under the shipped matrix config both phase-2 contexts carry a non-None store, so it never executes. Recorded so it is not re-chased. |

### Magnitude honesty notes
- Do **not** oversell #1's raw "1.3–2x" — the pool already saturates cores, so it is a
  contention win (~3–12%), not an idle-box recovery.
- #2 is tail-only and collapses at the script default `--top-n 12` (one wave).
- #3/#4/#6 are sub-1% each — "multiple small things," not headline levers.
- The phase-2 backtests already ride the shipped `c1/c5/c18/c19/c30/c31/c29` wins and the
  47x matrix lever; there is no second large multiplier hiding here.
