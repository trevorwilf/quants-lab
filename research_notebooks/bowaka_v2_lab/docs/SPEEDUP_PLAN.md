# fast_realism 5000-Trial Study — Relaunch Speedup Plan

*Produced 2026-06-16 by a comprehensive parity-aware investigation (14-surface discovery →
dedup → adversarial verify → synthesize; 53 agents). Every claim was adversarially
verified against the live code; "adjusted impact" = the realistic figure after that scrutiny
(several discovery claims were corrected down).*

**Baseline:** ~26 days, 16 process-parallel workers, ~120 min/trial. Verified against
`configs/_fr_study_resolved.yml:65–99`.

---

## Headline

**The ~26-day runtime is dominated by a single trivial config omission.** The live
fast_realism config's `optuna.acceleration` block contains **only `scan_matrix`**
(`_fr_study_resolved.yml:66–81`). The three per-trial DQ/IO caches —
`startup_dq_cache`, `batch_daily_cache`, `session_minute_window_cache` — **and** the
`pruning` block exist in the codebase, are parity-tested, and are enabled in the
current_code_parity matrix overlay, but **were never copied into the fast_realism config.**

With the DQ cache OFF, **~93% of every trial is the per-fold data-quality rebuild**
(`build_data_quality_report`: ~24k daily-parquet re-reads + heavy pandas over ~1,966 symbols
per fold). And because that work is memory-bandwidth-bound, 16 workers each re-reading ~24k
partitions/fold create severe contention — which is *why* the single-thread ~30 min/trial
balloons to ~120 min observed. Enabling the cache (3 lines × 2 files) relieves **both** the
per-worker cost and the contention multiplier.

**Enabling it: ~26 days → ~2–3 days, byte-identical results.** Everything else is the long tail.

---

## 1. Baseline — where the ~120 min/trial goes

Arithmetic (consistent three ways): 26 d × 1440 = 37,440 wall-min × 16 workers = 599,040
worker-min ÷ 5000 trials = **~120 min/trial** = ~60 min/fold (2 folds/trial; Feb 19 + Mar 22
= 41 sessions = the matrix store).

Single-thread probe on ql-jupyter:

| State | per session | per trial (1-thread) | composition |
|---|---|---|---|
| **As-shipped** (DQ cache OFF) | 43.7 s | ~30 min | **~93% per-fold DQ rebuild**; scan eval only ~3.4 s, exits negligible |
| **Caches ON** (the cure) | 1.68 s | ~69 s | **~26× drop.** Residual: vectorized scan eval (dominant), exits, `build_code_manifest` (~5.5 s/fold), per-session setup |

**Structural facts:** scan matrix (47×) is enabled here; DQ-cache machinery (5.70×/fold) is
built but **not enabled**; 2 folds/trial; **no pruning**; fixed `n_trials=5000`; and workers
call `load_study()` **without a sampler** → they silently run Optuna's *default* TPESampler
(univariate, 10 startup), not the configured multivariate/500/1337 (see c3).

> The c1 cache flags are NOT in the matrix `config_input_hash`, so the **already-rebuilt,
> CA-current FR matrix stays valid** — c1 does not require a matrix rebuild.

---

## 2. Strict-parity wins (identical finalists; free speed)

Listed largest-first. **Everything below c1 is measured against the caches-ON residual
(~69 s/trial); until c1 lands they're buried under the DQ rebuild and unmeasurable.**

| # | Win | Adjusted impact | Effort | Files |
|---|---|---|---|---|
| **c1** | **Enable the 3 DQ/IO caches in the FR config** | **THE lever — ~26× single-thread; ~5–15× study wall-clock** | **Trivial** (3 lines × 2 files) | `_fr_study_resolved.yml:66–81`, `_fastrealism_study.yml`; machinery `fold_context.py:349–353`, `backtester.py:564,808–811` |
| c4 | Vectorize the per-symbol skip/reject loop in `evaluate_one_scan_vectorized` (numpy masks, first-match precedence, iterate only passing) | ~1.2× per-trial (~12–14 s) | Medium (~1 d) | `scan_matrix_vectorized.py:368–426` |
| c18 | Memoize `sym_to_idx`/`order_idxs` on the per-session scan context | ~3.8% (~2.6 s/trial) | Low | `scan_matrix_vectorized.py:232–237` |
| c29 | `lru_cache` `max_hold_exit_session`; skip redundant `sort_values` when monotonic; hoist fold-constant exit config | ~2–5% | Low–med | `exits.py:146,705–770,1087–1141` |
| c5 | Gate per-fold manifest/lineage block on `artifact_mode=='full'` | ~0.2–0.5 s/trial (real host; the 11 s was a container `git status` timeout) | Low | `backtester.py:1855–1932` |
| c17 | Cache opened `ScanMatrixSession` on the fold context (avoid 41 parquet reads/trial) | ~0.2–0.5% | Small–med | `fold_context.py:458` |
| c6 | Hoist `resolve_signal_fade_active` (incl. per-call `Path.exists()`) out of the per-event exit loop | ~0.1–1 s/trial (native FS) | Low–med | `exits.py:251–319,716–730` |
| c21+c22+c23 | Reuse `eligible_symbols_by_session`; memoize trial-invariant universe preamble + lineage halves on ctx | ~50 ms/trial combined | Low | `walkforward_runner.py:716–718`; `backtester.py:198–219`; `lineage.py:138–146` |
| c30 | Hoist `walk_until`→int64-ns out of the per-lot loop | ~0.3–0.8% | Low | `backtester.py:1299–1335` |
| c19 | Compute `score_vec` only for passing symbols (fold into c4) | ~0.3 s/trial | Low–med | `scan_matrix_vectorized.py:311–315` |
| c31 | Gate remaining ungated per-event allocs on `collect_event_log` (keep the side-effecting `step` calls) | ~50–80 ms/trial | Low–med | `backtester.py:1372–1392` |
| c9 | Dynamic work-queue / global-stop replacing static split + blocking join | ~3–6% steady-state **+ recovers a stranded tail if a worker dies** | Medium | `parallel.py:149–204` |
| c10 | Periodic `malloc_trim(0)` per-K-trials in the worker | **Not per-trial speed** — bounds the ~17 GiB/hr RSS climb so the study stops hitting the RAM wall that forces restarts (each restart re-pays cold imports + ctx build). High operational value | Low | `parallel.py:88–146` |
| c20, c24 | Bundle the auctions supplier; cache `parity_proof.json` at store-open | µs–ms/trial (hygiene; take only if already in the file) | Low | — |

**Compounding:** c4 (1.2×) × c18 (1.04) × c29 (1.03) × [c5+c17+c6+c19+c30+c31+c21+c22+c23 ≈ 1.03]
≈ **~1.32× on the post-c1 residual (~24% per-trial cut)**, none overlapping c1 or each other.

---

## 3. Methodology trade-offs (faster, but alters the search → different finalists)

None are bit-parity; all need a fresh study. **Apply only with sign-off after Groups 1–4.**

| # | Win | Adjusted impact | What it trades |
|---|---|---|---|
| **c2** | Reduce `n_trials` 5000 → ~1500–2000 (after a 500-trial pilot to confirm the best-value plateau) | **60–70% wall-clock**, multiplies cleanly with per-trial wins | Search depth. The finalist stage only *validates/records*, it does **not** refine — fewer trials → different best trial. No wired plateau detector (pilot is manual). |
| **c3** | Fix workers to use the **configured** sampler (multivariate, 500 startup, seed 1337+worker) — they silently run the default today | Sample-efficiency only; discount to single-digit–~20% **and unproven on this objective**; direction not guaranteed | Different trajectory; also fixes a false provenance claim. Needs a unit test + per-worker seed offset. |
| c7 | Conservative catastrophic-floor pruning (`floor ~-1.40`, `min_completed 30–100`) | ~3–12% (a clean no-trade fold scores exactly −1.0 and does NOT prune) | Pruned trials change the TPE surrogate set. **Calibrate the floor from a real fold-0 distribution, not the −1.5 comment.** |
| c14 | Single fold during search (rank on the larger March fold), 2-fold+holdout at finalist | ~46% per-trial during search | Zeroes cross-fold variance penalty; concentrates on one ~1-mo regime (overfit); high effort |
| c13 | Per-study plateau early-stop | ~0 to ~60% (variable) | Overlaps c2; hurts reproducibility (racy stop). Prefer c2. |
| c12 | Tighten over-wide bounds toward live | ~5–12% fewer trials | **Candidate's concrete bounds use STALE anchors** (would exclude the true `max_quote_age_seconds=104`) — re-derive from the live contract first |
| c11, c15 | Freeze low-value dims / cut n_startup | ≈0% | No-ops on a fixed budget / workers already use default startup |

---

## 4. Projected ETA (conservative; per-trial wins multiply, methodology multiplies on top)

**Scenario (a) — strict-parity only (identical finalists):**
```
Baseline                                   26.0 d
c1 (DQ caches)         ÷ 8× (mid of 5–15) → 3.25 d
per-trial stack (c4·c18·c29·smalls·c9) ÷ 1.37× → 2.37 d
c10                    removes restart tax (operational)
```
→ **~26 days → ~2–3 days, byte-identical** (≈1.7 d if c1 hits 12× and the stack ~1.4×).

**Scenario (b) — + methodology:**
```
Scenario (a)                               ~2.37 d
c2 (5000→2000)         × 0.40            → ~0.95 d
c3 + c7 (conservative) × 0.90            → ~0.85 d
```
→ **~1 day (~20–24 h)**, *contingent on the c2 pilot confirming a plateau* and accepting
non-identical finalists. If no plateau, hold 5000 and fall back to ~2.4 d.

**c1 alone does ~85% of the work.**

---

## 5. Recommended implementation order (ship in measurable groups; measure before trusting)

- **Group 0 — de-risk (parity-safe, alongside Group 1):** add `market_data.shared_root:
  /opt/market_data_cache` so c1's DQ-cache `lake_root` key matches across all 16 spawn
  workers (the historical cache-miss footgun); add the `effective_n_jobs == n_jobs`
  fail-loud assert.
- **Group 1 — c1, alone.** Add the 3 cache flags. **Measure:** (1) fast_realism off-vs-on
  objective identical within 1e-9 (the existing parity test runs against CCP, not FR — close
  that gap); (2) `startup_dq_cached_hits > 0` on the first ~5 trials (the cache build swallows
  errors + silently falls back → no parity risk but no speedup); (3) per-session ~43.7 s →
  ~1.7 s (≥10×). Trust only when per-session drops ≥10× AND the objective is identical.
- **Group 2 — cheap parity batch:** c5, c18, c21, c22, c23, c20, c17, c30, c31, c6. Measure
  warm single-fold cProfile + wall-time before/after; run the full ~450-test parity suite
  (must be byte-identical); add parity tests for new ctx memos.
- **Group 3 — c4 + c19** (the numpy vectorization, ~1 day): mask-based, first-match
  precedence. Measure the rejection-count + tie-order + full-fold parity tests (byte-identical).
- **Group 4 — c10 then c9:** ship `malloc_trim` first (RSS plateaus instead of climbing
  ~17 GiB/hr); then the dynamic queue (stop overshoot ≤15; killed worker no longer strands).
- **Group 5 — methodology (operator sign-off, fresh study):** c3 first (+ a worker-sampler
  unit test) → c2 500-trial pilot (set 1500–2000 only if the curve plateaus) → c7 (calibrate
  the floor from a real fold-0 distribution). Skip c13/c11/c12/c15.

---

## 6. Do-not-pursue

- **Already shipped (no further win):** scan_matrix 47× (enabled), DQ-cache machinery, sim
  exit-path, numba build kernels, objective_minimal, cached_suppliers, opt #1 (`_log_event`
  gate), Opt A/B/C in the scan eval, `_forward_window` (opt #2), `_normalise_bars` dtype path.
- **Rejected (real=false or ≈0):** c16 parent-as-17th-worker (RAM-bound at 8–11 workers in
  the 157 GiB container, not core-bound); c15 (no-op); c11 (0% on fixed budget; wrong premise);
  c26 daily-LRU (subsumed by c1); c27/c28 (below noise); c33 attr consolidation (parity-fragile);
  c24/c32/c20/c25 (µs–s; opportunistic only).
- **Per prior analysis (don't re-hunt):** a second 47×-class lever; intended_realism timing
  probes (infeasible on the illiquid universe); default-ON numba for the study (build-only).

**Bottom line: do c1 + measure first.** ~26 days → ~2–3 days at strict parity from one
trivial config fix; the dozen small wins compound to ~2 days; piloted methodology lands ~1 day.

---

## 7. Implementation status — 2026-06-16 (committed on dev: 6de20b6; phase-2 follow-up 97b2cbc)

User directive: "fix the bug first, then continue with the recommended plan; do NOT do
the methodology levers (Group 5)." A 16-agent Group-2/3/4 recon (verify each candidate
against live code) drove the skips below. Verified: **257 unit + 252 parity + 21
integration tests pass**; the only 3 failures pre-exist and are unrelated (frozen-contract
source_manifest drift on the prod mirror `bowaka_v2_backtest.py`, clean-vs-HEAD but drifted
vs the committed contract; + the pre-modified notebook-10 default-config tests — none read a
file this work touched).

**SHIPPED (byte-identical, parity-proven):**
- **c3 (the bug)** — workers now reconstruct the configured sampler (`build_worker_sampler`,
  multivariate + configured startup + per-worker seed offset) instead of Optuna's default.
- **Group 0** — `market_data.shared_root: /opt/market_data_cache` in both FR configs
  (**this was a REQUIRED relaunch blocker**: `MARKET_DATA_ROOT` is unset in the container
  after the volume-migration recreate, so the FR config resolved the slow 9p lake →
  `config_input_hash` mismatch → fail-loud matrix-miss; `shared_root` reproduces the built
  matrix's hash `283fce5d…` exactly). Plus the `effective_n_jobs != n_jobs` fail-loud assert
  (strict-gated + warn).
- **c1** — the 3 DQ/IO cache flags. **A/B measured (FR split-0, 1,966 syms): per-fold
  909.8 s → 45.2 s = 20.14×, `full_builds=0 / cached_hits=1`, FoldResult BYTE-IDENTICAL.**
  Both gates (≥10× + identical objective) pass under fast_realism. Matrix stays valid.
- **c5, c18, c19, c30, c31, c29(only the `lru_cache`)** — parity-proven.
- **c10** + **c9 liveness slice** (`_drain_worker_results` — a dead/OOM'd worker no longer
  deadlocks the drain).

**SKIPPED (recon-driven):** **c4** — the plan's biggest post-c1 win (~1.2×), but prior
Opt A/B/C + the scan-floor skip already removed the heavy per-symbol work (gain
"questionable") and vectorizing the reject loop risks `gate_dump` order/payload drift (HIGH
risk). **c22, c23** (premise wrong / `dataset_hash` not trial-invariant / ~0 net gain).
**c6** (FR has `max_concurrent_positions: 1` → resolver fires ≤1 lot/tick, negligible).
**c21** (~tens of ms; not worth disambiguating two near-identical hot paths).
**c29(B)** sort-skip — NOT parity-safe (unstable quicksort reorders ties). **c29(C)** — no-op.

> **Revised compounding:** without c4, Group 2–4 add ~**1.10–1.13×** per-trial (not the
> earlier ~1.32×). c1 remains ~85% of the win: **~26 d → ~3 d** strict-parity.

**DEFERRED (medium-risk, operator call):** **c17** (cache the opened `ScanMatrixSession`
per session on the ctx — the plan's cited site was wrong; the real fix threads a new
frozen-ctx field through 3 files for only ~0.2–0.5%). **c9 dynamic-rebalance** (the
atomic-counter work-queue, ~3–6%; the high-value liveness slice already shipped).
