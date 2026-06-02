# Notebook 10 walk-forward speedup — scan-matrix runtime + pruning

Phase notes for `bowaka_v2_lab_optuna_walkforward_scan_matrix_speedup_claude_code_prompt.md`.
Goal: cut per-trial wall-clock from ~30–45 min toward ≤3 min by enabling the
already-parity-proven scan-matrix **vectorized** runtime (shipped but config-off)
behind a dedicated overlay with a live parity gate, plus fold-level pruning and a
measurement harness. No new strategy logic; no parity/holdout contract loosened.

Branches off `dev`; each phase merged `--no-ff` after testing. The pre-existing
WSL failure `tests/integration/test_full_test_matrix_dry_run.py::
test_full_test_matrix_dry_run` is ignored per §0.2.

**Known pre-existing failures on this workstation (NOT caused by this work)** —
present on `dev` before any phase branch, in files this work never touches:
- `tests/unit/reference/test_prod_backtester_default_uses_lake.py` (2) +
  `tests/integration/test_prod_backtester_rejects_megacaps_via_price_gate.py` +
  `tests/integration/test_prod_backtester_synth_flag_still_works.py` — all
  inspect/run the **gitignored** prod mirror `reference/source_strategy/scripts/
  bowaka_v2_backtest.py`; the local mirror predates the parity-speedup prod
  vectorize work, so `_make_lake_suppliers` is absent. Out of scope (this work
  never edits `reference/` — verified `git diff --stat dev -- reference/` == 0).
- 5 lab-vs-production PARITY tests (the **out-of-scope notebook-13 path**, §0.6):
  `tests/integration/test_parity_cli_subcommand.py`,
  `test_parity_notebook_papermill_runs_headless.py` (×2),
  `test_parity_parallel_matches_serial.py`,
  `test_parity_runner_against_real_lake.py`. Root cause (read live): the prod
  side errors `bowaka_v2_backtest.py: error: unrecognized arguments:
  --lake-root` — the gitignored mirror predates the PREVIOUS session's
  `ea1c942` ("run_lab_backtester lake-root threading"), which made the lab pass
  `--lake-root` to it. Pre-existing + environmental (operator must re-sync the
  mirror); provably independent of this work — the parity path uses
  `run_lab_backtester → run_backtest` with NO `scan_matrix` block, so the matrix
  is never active and this work's only shared change (the `matrix_scans_evaluated`
  counter, gated on `_matrix_scan_result is not None`) never executes there.
- `tests/unit/test_notebook_bootstrap_cell.py` — `13_lab_vs_production_parity.ipynb`
  (dirty working-tree smoke output from a prior session) + the stray tracked
  `Untitled.ipynb`. Notebook 13 is explicitly out of scope (§0.6).

---

## Phase 1 — Store-root wiring hardening (resolver + fail-loud) — 2026-06-02

**Branch:** `speedup/wf-phase1-store-root-resolver` (off `dev`).
**Effort:** medium.

**Problem fixed.** `optuna/fold_context.py` read the scan-matrix store path as
`sm_cfg.get("store_root")`, but every committed config writes the key as `root:`
(the base `.../cache/scan_matrix`, no scope suffix). The read therefore resolved
to `None` and the matrix never fired — and a broad `except: scan_matrix_store =
None` would have silently degraded an *enabled* study to the slow legacy scanner
even with a built matrix present. A multi-hour build could be ignored with no
signal.

**What changed.**
- `src/bowaka_v2_lab/scanner/scan_matrix.py` (+43 lines): new module-level
  `resolve_scan_matrix_store_root(sm_cfg, scope)`. Resolution order
  `store_root` → `root` (back-compat) → `None`; appends `/<scope>` unless the
  path already names it (so base `root:` and suffixed `store_root:` land on the
  same built location); resolves repo-relative paths absolute against the repo
  root (`parents[5]`, the same anchor `build_scan_matrix` uses). Added to
  `__all__`.
- `src/bowaka_v2_lab/optuna/fold_context.py` (net +71 lines): new helper
  `_open_fold_scan_matrix_store(cfg, scope)` replaces the inline raw-read +
  broad-except block in `_build_one_fold_context`. It returns `None` (legacy
  scanner) ONLY for the deliberate cases — runtime not enabled, `runtime_mode:
  disabled`, no path configured at all, or the **holdout** scope under
  `separate_holdout_matrix` (holdout isolation: the holdout window is never read
  from a matrix during tuning / finalist evaluation). When the runtime is
  enabled and a store IS configured but cannot be opened, it raises
  `OptunaStudyInvalidError` with the path tried, the scope, and the exact
  `scan-matrix build` + `verify` commands — fail loud, never silent-degrade.
  Threaded `scope` through `_build_one_fold_context` (`build_fold_contexts`
  passes `"validation"`, `build_holdout_context` passes `"holdout"`). `_prune_cb`
  and every other behaviour untouched.

**No committed config changed** (`enabled`/`runtime_mode` stay as-is; the resolver
just reads the existing `root:` key now). Behavioural no-op for every committed
config because all have the matrix `enabled: false`.

**Tests added.**
- `tests/unit/scanner/test_resolve_scan_matrix_store_root.py` (7) — store_root
  verbatim-when-scoped, scope-suffix-when-absent, root fallback, store_root
  preferred over root, neither→None (incl. empty string), repo-relative→absolute,
  holdout segment.
- `tests/unit/optuna/test_fold_context_scan_matrix_fail_loud.py` (8) —
  enabled+vectorized / enabled+compatibility + missing store → raises (actionable
  message); disabled runtime_mode / not-enabled / unconfigured → None no-raise;
  holdout isolated → None even if configured; holdout w/o separation → raises;
  present manifest → opens + returns store.

**Test results.** New tests: 15/15 pass. `tests/unit/optuna` + `tests/unit/scanner`:
415 pass. scan_matrix/fold_context-filtered integration (`-k "scan_matrix or
fold_context or runtime_mode"`): 24 pass. Full unit+parity: 1432 pass, 1 skip
(modulo the 5 pre-existing unrelated failures above). Integration+reconcile leg:
all tests up to 75% passed with **zero FAILED/ERROR**, then one *real-lake* test
(`test_walkforward_worker_finds_trades.py::
test_single_session_produces_nonzero_candidates`) stalled out at the 600s
timeout inside `os.stat` on a `MarketDataStore.minute_bars` `path.is_file()`
lake read — a host-I/O-contention timeout (this workstation runs live trading +
the lake on local disk), in the **legacy `evaluate_one_scan` path with the
matrix disabled**, independent of this phase. On Windows the pytest-timeout
`thread` method terminates the whole session, so the leg aborts there.

**Testing strategy (host-constrained).** This workstation is load-contended
(live trading + the lake on local disk), so the full real-lake integration suite
is not reliably completable in one shot — a single real-lake test can stall in
`os.stat` for >600s. Per phase: full unit+parity + the change-relevant
integration subset; the comprehensive `make test-all`-equivalent runs at the
Phase 4 acceptance gate. Any environmental real-lake timeout is treated like the
§0.2 pre-existing-WSL exemption (not a phase-caused failure).

**Files+lines:** scan_matrix.py +43, fold_context.py +90/-19. Diff: 2 files,
114 insertions / 19 deletions (+ 2 new test files).

**Merge SHA:** recorded in the final status block (Phase 4).

---

## Phase 2 — Enablement overlay + live parity gate — 2026-06-02

**Branch:** `speedup/wf-phase2-matrix-overlay-parity` (off `dev`, Phase 1 merged).
**Effort:** high (live build/verify + end-to-end parity assertion).

**What changed.**
- `configs/bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.yml` (NEW)
  — the ONLY committed config that turns the vectorized runtime on
  (`enabled: true`, `runtime_mode: vectorized`, `require_parity_manifest: true`,
  `store_root: .../scan_matrix/validation`, `scope: validation`,
  `separate_holdout_matrix: true`, `allow_full_history_matrix: false`,
  `build_if_missing: false`). A full standalone copy of the workstation overlay
  (there is no YAML inheritance) with a header documenting the build→verify
  preconditions. Validates (`BowakaV2Config.model_validate`) + passes `env-check`
  (the `acceleration` block is a free-form `dict[str, Any]`, so `store_root` is
  accepted).
- `tests/integration/test_scan_matrix_runtime_mode_disabled_is_default.py` —
  the default-disabled sweep now EXCLUDES `*matrix*.yml`; added a positive test
  asserting the overlay enables `vectorized` + `require_parity_manifest` + a
  `/validation` store_root + `separate_holdout_matrix`.
- `src/bowaka_v2_lab/utils/profile_counters.py` (+7) — new `matrix_scans_evaluated`
  counter (explicit "the matrix fired" signal).
- `src/bowaka_v2_lab/sim/backtester.py` (+9) — bump `matrix_scans_evaluated` once
  per scan the matrix actually serves (override produced). A silent legacy
  fall-through leaves it at 0.
- `tests/integration/test_scan_matrix_walkforward_fold_parity.py` (NEW, `slow`) —
  the live parity gate: builds a tiny matrix on a synthetic intraday lake,
  verifies it (`--vectorized-check` → `verifier_version == 2`), then runs ONE
  validation fold two ways via `build_fold_contexts` → `run_backtest`:
  `runtime_mode: disabled` (legacy) vs `vectorized` (matrix). Asserts the matrix
  FIRED (`matrix_scans_evaluated > 0` on vectorized, `== 0` on disabled) and the
  backtest summary is reproduced EXACTLY (zero field diffs, `net_return` 1e-9).

**Live-build finding (validates the prompt's "operator step" framing).** A real
validation-scope build is genuinely multi-hour: a CC-run small build on the
operator's lake measured **~98 min for 23 sessions × 3 symbols** at 60s cadence
(the per-`(scan_ts, symbol)` feature recompute over real minute parquets, ×
~346 scans/session × 23 sessions, on a load-contended host). So the test uses a
**synthetic intraday lake** (cheap reads → seconds) under `current_code_parity`
mode (the intraday-scanner path; `smoke_fixture` uses a daily driver that never
fires the matrix) — deterministic + reproducible on any host, no real-lake
dependency. The verify→`verifier_version=2` path (the small-build proof) was
exercised live on BOTH the synthetic and the real lake. The full validation-scope
build is the operator step in `docs/walkforward_scan_matrix_runbook.md` (Phase 4).
The candidate/trade-level three-way parity (legacy == compat == vectorized) is
covered exhaustively by `tests/parity/test_scan_matrix_vectorized_*`; this gate
covers the fold-context → backtester WIRING + summary parity those don't.

**Test results.** Overlay validates + `env-check` ok. Sweep + positive + shipping
validate: 47 pass. Fold-parity gate: PASS in 39s
(`matrix_scans_evaluated`=6920 vs 0; zero summary diffs). `tests/parity` +
`tests/unit/scanner` + `tests/unit/utils` (touched-file regression): 428 pass.
Integration `-k "scan_matrix or backtest or fold_context or runtime_mode or
shipping_configs"`: 86 pass, 1 skip, 2 pre-existing prod-mirror failures (above).

**Files+lines:** new overlay config, new fold-parity test, sweep test updated,
backtester.py +9, profile_counters.py +7.

**Merge SHA:** recorded in the final status block (Phase 4).

---

## Phase 3 — Fold-level pruning + per-trial measurement harness — 2026-06-02

**Branch:** `speedup/wf-phase3-pruning-and-measure` (off `dev`, Phase 2 merged).
**Effort:** medium.

**What changed.**
- `optuna.pruning` block added to BOTH the base workstation config AND the
  matrix overlay: `enabled: true`, `min_completed_trials_before_pruning: 30`,
  `catastrophic_floor: -1.40`. The objective's existing `_prune_cb`
  (`make_walkforward_objective`) already reads these keys — its LOGIC is
  unchanged; only the config values are added.
- `scripts/benchmark_walkforward_trial.py` (NEW) — runs a small study (default
  `--n-trials 8`) against the matrix overlay, reads
  `artifacts/optuna/<study>__phase_profile.json`, prints mean per-trial
  wall-clock, the `phase_seconds` breakdown, the `scanner_symbols_seen`
  (legacy scan work — collapses when the matrix is active) +
  `matrix_scans_evaluated` counters, peak RSS, and the projected
  `--target-trials` (default 5000) budget at the config's `n_jobs`, with a
  one-line verdict vs the <=3 min/trial goal. `--legacy` re-runs with
  `runtime_mode=disabled` for an A/B speedup ratio.

**Floor justification.** The incumbent objective is ~ -1.05; a no-trade /
degenerate fold scores ~ -1.5 (the `low_trade_count` penalty maxes at 1.0 plus
the other penalties — matches the observed all-zero-trade `value=-1.5` studies).
`catastrophic_floor: -1.40` therefore sits in the dead band: above the no-trade
floor and well below the incumbent, so a trial is pruned ONLY once its running
score is already worse than anything plausibly promotable after a fold.
`min_completed_trials_before_pruning: 30` keeps the full TPE startup window
(`n_startup_trials: 25`) explore-only.

**Tests.**
- `tests/unit/optuna/test_pruning_floor_config.py` (6) — both shipping configs
  carry the exact pruning block (enabled / min 30 / floor -1.40 in the
  conservative band); the `_prune_cb` prunes a no-trade running score (< -1.40),
  spares an incumbent-like score, and is a no-op inside the startup window — at
  the SHIPPING floor value (the generic mechanism stays covered by
  `tests/integration/test_pruning_catastrophic_floor.py`).
- `tests/unit/scripts/test_benchmark_walkforward_trial_smoke.py` (4) — script
  exists, import-clean (heavy study import deferred), `--help` exits 0, defaults
  parse.

**Test results.** New tests 9/9 pass. Config sweeps (validate + disabled-default
+ existing pruning) + the benchmark CLI `--help`: 55 pass. Full `tests/unit`:
1227 pass, 1 skip (modulo the 5 pre-existing unrelated failures). Zero `src/`
behaviour changes (pruning logic pre-existed; only config values + new
script/tests added).

**Merge SHA:** recorded in the final status block (Phase 4).

---

## Phase 4 — Verify target + operator runbook + final status — 2026-06-02

**Branch:** `speedup/wf-phase4-verify-and-runbook` (off `dev`, Phase 3 merged).
**Effort:** medium.

**What changed.**
- `Makefile` — new `make verify-walkforward-speedup` target (added to `.PHONY`).
  Runs the Phase 1 resolver + fail-loud tests, the Phase 2 default-disabled
  sweep + matrix-overlay positive tests + the end-to-end fold-parity gate, the
  Phase 3 pruning-config test, and the benchmark smoke — test files named by
  PATH so the `slow`-marked parity gate runs too. Prints `Walkforward speedup
  wiring: OK` on success / `FAIL (pytest exit=N)` on failure; **41 pass in ~37s**
  (well under the <2 min budget).
- `README.md` — a "Walk-forward scan-matrix speedup verification" section beside
  the `verify-bayesian-fix` / `verify-session-window-parity` entries: the
  target, what it covers, and the build → verify `--vectorized-check` →
  use-the-overlay enablement preconditions.
- `docs/walkforward_scan_matrix_runbook.md` (NEW) — dense operator runbook:
  full validation-scope build (+ the optional `/opt/market_data_cache` 9p cache
  note), verify + `verifier_version == 2`, the per-trial benchmark, the fast
  study, the 5000-trial budget table, the holdout / search-space / fail-loud
  safety contracts, and the rebuild triggers.
- Cleanup: no `STATUS_BLOCKED_phase*.md` were ever created (no phase hit the
  5-attempt block).

**Merge SHA:** this branch's merge into `dev` (the final merge below).

---

## Final status — all four phases merged to `dev`

| Phase | Branch | Merge SHA |
|---|---|---|
| 1 — store-root resolver + fail-loud | `speedup/wf-phase1-store-root-resolver` | `c8446b4` |
| 2 — enablement overlay + live fold-parity gate | `speedup/wf-phase2-matrix-overlay-parity` | `4eda848` |
| 3 — fold-level pruning + per-trial benchmark | `speedup/wf-phase3-pruning-and-measure` | `cde6446` |
| 4 — verify target + runbook + final status | `speedup/wf-phase4-verify-and-runbook` | `2b0d56b` |

**One-line summary.** The parity-proven scan-matrix vectorized runtime (shipped
but config-off) is now correctly wired (store-root resolver + fail-loud), enabled
behind a dedicated overlay with an end-to-end fold-parity gate proving it FIRES
and reproduces the legacy fold exactly, multiplied by conservative fold-level
pruning, and made re-checkable (`make verify-walkforward-speedup`) + operable
(runbook + benchmark). `main` untouched throughout.

**Measured per-trial number.** Not measured end-to-end in CC: a full
validation-scope study requires the multi-hour operator build (measured **~98
min for 23 sessions × 3 symbols** at 60s cadence on the operator lake — the
empirical confirmation that the full build is an operator step, not a CC step).
The matrix path is PROVEN to fire and to be transparent: the fold-parity gate
shows `matrix_scans_evaluated = 6920` on the vectorized run vs `0` on the
disabled run with a **byte-identical backtest summary**, and `scan-matrix verify
--vectorized-check` was exercised live to `verifier_version == 2` on both a
synthetic and the real lake. **Operator to measure the real per-trial wall-clock
via `scripts/benchmark_walkforward_trial.py --legacy`** after the full build (the
`<=3 min/trial` target + A/B speedup ratio print automatically).

**Final test-all on `dev` HEAD (modulo §0.2 + the pre-existing exemptions above).**
- Full unit+parity: **1443 pass, 1 skip** (modulo the 5 pre-existing unit
  failures: 2 prod-mirror + 3 notebook-bootstrap).
- Integration+reconcile: **466 pass, 8 skip, 7 failed** — all 7 pre-existing /
  environmental (5 out-of-scope parity tests blocked by the stale prod mirror's
  missing `--lake-root`; 2 prod-mirror), plus one real-lake test
  (`test_walkforward_worker_finds_trades`) deselected because it stalls >900s in
  a `pyarrow.parquet.read_table` / `os.stat` lake read on this load-contended
  workstation (live trading + lake on local disk) — the Windows pytest-timeout
  `thread` method then kills the whole session, so the full real-lake leg is not
  reliably completable here in one shot. With that one staller deselected the
  leg ran to completion (466 pass).
- `make verify-walkforward-speedup`: **41 pass in ~37s** (<2 min).
All 7 integration + 5 unit failures are unrelated to this work — verified
logically (the parity / prod-mirror paths never activate the matrix, so the
shared `run_backtest` counter change is a no-op there) AND empirically (the
parity failures are the prod mirror rejecting `--lake-root` from `ea1c942`;
`git diff --stat dev -- reference/` == 0; no notebook edits).
