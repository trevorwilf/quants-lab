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
- `tests/unit/reference/test_prod_backtester_default_uses_lake.py` (2 tests) —
  inspect the **gitignored** prod mirror `reference/source_strategy/scripts/
  bowaka_v2_backtest.py`; the local mirror predates the parity-speedup prod
  vectorize work, so `_make_lake_suppliers` is absent. Out of scope (mirror is
  never edited by this work).
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
