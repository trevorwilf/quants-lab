# Walk-forward Numba kernels — phase notes

Port of market_lab's parity-gated `@njit(cache=True)` kernel pattern into the
bowaka_v2 walk-forward path. Compiled kernels are a constant-factor lever that
COMPLEMENTS the scan matrix (algorithmic lever). Default OFF, flag-gated
(`optuna.acceleration.numba.enabled`), pure-Python fallback when numba is absent.
No `fastmath`/`parallel`; recursive EMAs are bit-exact, sums use the canonical
sequential order (≤1e-10 drift, as market_lab's `bbp` kernel).

---

## Phase 1 — Numba infra + scan-feature kernels (faster matrix build/rebuild)

**Branch:** `speedup/numba-phase1-scan-feature-kernels` (off `dev`). Merge SHA: see finalize.
**Effort:** high. **numba in test env:** 0.61.2 (kernels compiled + benchmarked for real).

### Files
- `src/bowaka_v2_lab/features/_numba_availability.py` (NEW) — shim ported verbatim
  from market_lab (`_NUMBA_AVAILABLE`, `NUMBA_VERSION`, `_numba=None` on ImportError).
- `src/bowaka_v2_lab/features/_numba_scan_features.py` (NEW, ~280 lines) — `njit`
  no-op fallback; `_ewm_mean_series` (reused verbatim from market_lab
  `_numba_indicators`, bit-exact vs `ewm(adjust=False)`); `_fallback_curve_fraction_nb`
  (exact `forming_bar._fallback_curve_fraction`); `_forming_features_nb` (the 8
  forming features — SHARED by build + legacy scan); `compute_baselines_nb`
  (exact `compute_prior_daily_baselines`: simple-mean TR/vol, span/adjust=False EMA);
  `build_session_columns_nb` (per-symbol batch over all scans: cumulative
  aggregate + fallback vcf + features → matrix-column layout with NaN/-1/0 defaults).
- `src/bowaka_v2_lab/features/forming_bar.py` — `compute_prior_daily_baselines(..., use_numba=False)`
  and `compute_forming_session_features(..., use_numba=False)` gain a kernel dispatch
  (default OFF; falls back when numba absent). Pure-Python bodies unchanged.
- `src/bowaka_v2_lab/scanner/scan_matrix.py` — `_numba_scan_features_enabled(cfg)` +
  `_baseline_scalar(...)` helpers; `build_session_partition` precomputes per-scan ET
  minute-of-day and, when enabled + a symbol has OHLCV, computes the per-symbol
  columns via `build_session_columns_nb` in one njit pass (sorted ascending by
  ns-UTC ts — forced ns to avoid the µs `astype` gotcha) instead of the per-scan
  pandas slice; else the existing loop (unchanged).
- `src/bowaka_v2_lab/scanner/scan_loop.py` — `evaluate_one_scan` reads the numba
  flag and threads `use_numba` into `compute_forming_session_features` (the SAME
  `_forming_features_nb` kernel the build uses → build-path and scan-path stay
  mutually parity-equal). Aggregate stays pandas (single-scan, cheap).
- `scripts/generate_numba_scan_feature_fixtures.py` (NEW) — seeded synthetic daily +
  minute bars → PURE-PYTHON baselines + per-scan build columns → `.npz`+JSON, S/M/L.
- `scripts/benchmark_numba_scan_features.py` (NEW) — pandas vs numba-first(JIT) vs
  numba-warm on a per-session symbol batch.

### Fixtures (committed, `tests/fixtures/numba_scan_features/`)
- small: 22 daily × 80 minute × 7 scans
- medium: 40 daily × 200 minute × 21 scans
- large: 80 daily × 390 minute × 84 scans

### Tests (25, all green)
- `tests/unit/scanner/test_numba_scan_feature_parity.py` (7) — `compute_baselines_nb`
  vs pure (rtol 1e-9, atol 1e-10 — covers the ~1e-16 rel drift on avg_dollar_volume)
  and `build_session_columns_nb` vs pure build columns (ints/bools exact; floats
  atol 1e-10 with NaN positions).
- `tests/integration/test_numba_scan_matrix_build_parity.py` (1, `slow`) — **LOAD-
  BEARING**: builds one session partition numba OFF vs ON on a tiny lake; every
  stored column byte-equal for ints/bools, atol≤1e-10 for floats; asserts the
  kernel path actually fired (`has_baseline` cells > 0). Proves enabling kernels
  does not perturb the matrix the runtime reads → the existing scan-matrix parity
  proof transfers. CANONICAL PROOF stays numba-OFF (`scan-matrix verify`).
- `tests/unit/test_numba_flag_default_off.py` (17) — every committed `bowaka_v2_*.yml`
  parses `numba.enabled` false; absent block reads false.

### Benchmark (numba 0.61.2)
20 symbols × 78 scans × 390 minute bars: pure-Python 0.3970 s → numba-warm 0.0012 s
= **325× warm** (target ≥10×). First call (JIT) 0.264 s. The warm win is the
per-session feature-compute delta the build amortizes; pre-warm the on-disk cache
(`warm_numba_cache.py`, Phase 3) before spawning Optuna workers.

### Comprehensive test gate
`tests/unit + tests/parity + tests/scanner + tests/reconcile` (`-m "not slow"`):
**1521 passed, 1 skipped**, modulo 4 PRE-EXISTING failures unrelated to this phase
(none touch files changed here): `tests/unit/reference/test_prod_backtester_default_uses_lake.py`
(×2, stale gitignored prod mirror) and `tests/unit/test_notebook_bootstrap_cell.py[10,13]`
(×2, the operator's dirty working-tree notebooks). Plus the §0.2 WSL
`test_full_test_matrix_dry_run`. Scan-matrix build/parity suite (incl. the existing
three-way parity, numba-OFF) re-run green (6 passed).

---

## Phase 2 — Sim inner-loop kernel — MEASUREMENT-GATED → **SKIPPED (documented)**

**Branch:** `speedup/numba-phase2-sim-exit-kernel` (off `dev`, documentation-only,
merged `--no-ff`). **Effort:** high.

### Measurement (gate task 0)
Read the matrix-overlay smoke `phase_profile.json`
(`artifacts/optuna/iex__bowaka_v2_iex_walkforward_conservative_ade3139f_20260603__phase_profile.json`,
1-trial `current_code_parity`, matrix vectorized).

`phase_seconds` (per study): finalize 5764.3s, **optuna_optimize 923.8s (= the 1
trial)**, fold_context_precompute 681.8s, preflight 291.1s, resolve_config 55.7s.

`counters` (post-matrix per-trial): scanner did **zero** work
(`scanner_symbols_seen=0`, all `scanner_time_*=0`; matrix served
`matrix_scans_evaluated=134940`). The per-trial residual is therefore 100% sim,
and it is dominated by **bar fetching / slicing / event processing**:
`bars_supplier_calls=5,069,287`, `bars_df_slices=4,130,026`,
`event_count_processed=3,793,064`, `minute_supplier_calls=270,242`. The numeric
bracket/time-stop comparison the proposed kernel would accelerate is a small
fraction; the cost is pandas data movement that happens OUTSIDE any njit kernel.

### Gate decision: SKIP the exit kernel
The sim dominates (gate's literal ≳40% criterion is met), **but the exit kernel's
callback-free path is never eligible in the target workload**, so it would buy ~0:

1. **Suppliers are wired on every `walk_lot_exit` call.** All three call sites
   (`sim/exit_driver.py:107`, `sim/backtester.py:466`, `:1191`) pass
   `quote_supplier=quote_supplier` and `signal_score_fn=...`, and the smoke proves
   they are live in the per-trial sim (`quote_supplier_calls=3276`). The kernel's
   eligibility predicate (`quote_supplier is None AND status_supplier is None AND
   signal_score_fn is None`, fade off) is thus FALSE for every per-trial call →
   the code MUST fall back to the pure-Python walk (prompt §1 caveat). The kernel
   would never fire.
2. **The dominant cost is bar fetching/slicing, not the bracket loop.** Even if a
   call were eligible, the kernel takes pre-extracted arrays; the 5.07M
   `bars_supplier_calls` + 4.13M `bars_df_slices` (the actual bottleneck) are the
   surrounding pandas plumbing, not the comparison the kernel speeds up.

Building it would add a parity surface (the prompt's biggest Phase-2 risk) for no
realized gain — the anti-pattern the gate exists to prevent. Per the gate
("skip the rest of this phase ... merge the empty-but-documented branch"), no sim
kernel is shipped. The real per-trial lever is reducing the bar-fetch/slice count
(the `session_window_cache` already absorbs 4.13M hits) — a different optimization,
not a numba kernel. Revisit only for a config/mode that runs `walk_lot_exit` with
NO live suppliers and fade disabled.

---

## Phase 3 — Wiring, pre-warm, deps, verify target, runbook

**Branch:** `speedup/numba-phase3-wiring-and-runbook` (off `dev`, merged `--no-ff`).
**Effort:** medium.

### Files
- `pyproject.toml` — `[project.optional-dependencies] numba = ["numba>=0.60.0"]`
  (`pip install -e .[numba]`); shim degrades gracefully without it.
- `scripts/warm_numba_cache.py` (NEW) — compiles + caches all 5 kernels on tiny
  inputs (warmed in 1.57 s) so spawned build/Optuna workers load the on-disk
  artifact instead of each re-JITing. Run once per env / after a kernel change.
- `configs/bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.numba.yml`
  (NEW) — the vectorized matrix overlay + `optuna.acceleration.numba.enabled: true`.
  The ONLY committed config that enables numba.
- `tests/unit/test_numba_flag_default_off.py` — base-config sweep now EXCLUDES
  `*numba*`; added positive tests (overlay enables numba + is still the vectorized
  matrix overlay; overlay excluded from the base sweep).
- `Makefile` — `verify-walkforward-numba` target (+ `.PHONY`): runs the parity +
  build-parity + default-off tests; prints `Walkforward numba kernels: OK` (<2 min).
- `docs/walkforward_numba_runbook.md` (NEW) — enablement, parity guarantees + how
  to re-prove (`verify-walkforward-numba`; `scan-matrix verify` stays numba-OFF as
  the canonical proof), measured deltas, lever order (matrix first).
- `README.md` — "Walk-forward numba kernels verification" section.

### Validation
- `warm_numba_cache.py`: 5 kernels compiled + cached in 1.57 s.
- verify-numba test set + shipping-config validate/env-check (incl. the new
  numba overlay): **67 passed**. The numba overlay validates + passes env-check.

### Per-trial number (gate task 6)
matrix-only ≈ matrix+numba **per trial** — numba is a BUILD-time lever (the trial
reads the prebuilt matrix; the Phase-2 sim kernel was skipped). The numba win is
the build feature-compute: **325× warm** (build benchmark). No `STATUS_BLOCKED_*`
files were created.

---

## Finalize — merge SHAs (all into `dev`, `main` untouched)

| Phase | Branch | Merge SHA |
|---|---|---|
| 1 — scan-feature kernels | `speedup/numba-phase1-scan-feature-kernels` | `5c288c8` |
| 2 — sim kernel (gate → skip, documented) | `speedup/numba-phase2-sim-exit-kernel` | `6422dfb` |
| 3 — wiring/deps/verify/runbook | `speedup/numba-phase3-wiring-and-runbook` | (this merge) |

**Final state:** scan-feature kernels ship default-OFF with a pure-Python
fallback + the LOAD-BEARING build-parity guard; the sim kernel is documented-out
by the measurement gate; numba is an optional extra with a pre-warm script, an
enablement overlay, a `verify-walkforward-numba` target, and a runbook. No base
config enables numba; the disabled-default invariant holds.
