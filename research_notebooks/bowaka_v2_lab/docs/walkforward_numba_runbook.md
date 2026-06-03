# Walk-forward Numba kernels — operator runbook

Compiled `@njit(cache=True)` scan-feature kernels (ported from market_lab's
parity-gated pattern) that make the **scan-matrix build/rebuild** materially
faster. Default OFF, optional dependency, pure-Python fallback. They are a
**constant-factor** lever that COMPLEMENTS the scan matrix (the **algorithmic**
lever, compute-once): build the matrix first; use kernels to shrink the build.

> **Lever order.** The matrix removes per-trial scan work (compute the features
> once, read memmap slices per trial). Numba kernels do not change the per-trial
> path (it reads the prebuilt matrix) — they make the one-time **build** faster
> by compiling the per-(scan, symbol) aggregate + feature math. Build the matrix
> first; reach for kernels to shrink the (weekly) build and rebuild.

## Enablement

```bash
cd research_notebooks/bowaka_v2_lab
pip install -e .[numba]                 # optional extra (numba>=0.60)
PYTHONPATH=src:../bowaka_common/src python scripts/warm_numba_cache.py
```

`warm_numba_cache.py` compiles + caches every kernel ON DISK once. Run it once
per environment and after any kernel change / numba upgrade — otherwise each
spawned Optuna/build worker pays first-call JIT. Then enable via either:

- **Overlay (committed):** build with the numba overlay
  `configs/bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.numba.yml`
  (= the vectorized matrix overlay + `optuna.acceleration.numba.enabled: true`), or
- **Run-time:** set `optuna.acceleration.numba.enabled: true` in your build config.

Without numba installed the flag is a no-op (pure-Python). Base configs keep it
OFF (pinned by `tests/unit/test_numba_flag_default_off.py`).

## What is compiled

`src/bowaka_v2_lab/features/_numba_scan_features.py` — reuses market_lab's
bit-exact `ewm(adjust=False)` recurrence; adds the bowaka forming features
(`_forming_features_nb`, shared by the build and the legacy scan), the fallback
volume-curve fraction, `compute_baselines_nb` (simple-mean TR / volume +
span/adjust=False EMA), and `build_session_columns_nb` (per-symbol batch over all
scans). Dispatch is wired in `build_session_partition` (the build hot loop),
`compute_prior_daily_baselines`, `compute_forming_session_features`, and the
legacy `evaluate_one_scan` — the build and scan share the SAME kernels, so they
stay mutually parity-equal.

## Parity guarantees + how to re-prove

```bash
make verify-walkforward-numba           # windows: PYTHON=C:/Python312/python.exe
```

Runs kernel-vs-committed-fixture parity (booleans/ints bit-exact, floats
`atol<=1e-10` with NaN positions) and the **LOAD-BEARING build-parity** test
(build one session numba OFF vs ON → every stored matrix column byte-equal for
ints/bools, `atol<=1e-10` for floats), plus the default-off invariant. Prints
`Walkforward numba kernels: OK` in <2 min.

- Recursive EMAs are **bit-exact** vs pandas. Sums (`session_volume`, the rolling
  means) use the canonical sequential order and match numpy/pandas to ~1e-13
  (within the 1e-10 tolerance), exactly as market_lab's Bollinger `bbp` kernel.
- **The canonical, kernel-independent matrix proof stays numba-OFF:**
  `python -m bowaka_v2_lab.cli scan-matrix verify --store-root <store> --config
  <config> --vectorized-check`. Build-parity proves OFF==ON, so that proof
  transfers to a numba-built matrix.

## Measured deltas

- **Build (where numba helps):** per-session feature compute (20 symbols × 78
  scans × 390 minute bars) — pure-Python 0.397 s → **numba-warm 0.0012 s = 325×**
  (`scripts/benchmark_numba_scan_features.py`; first call includes JIT ~0.26 s).
  The realized full-build delta is bounded by the feature-compute share of the
  build vs lake I/O (numba does not touch parquet reads).
- **Per trial: unchanged.** The matrix is prebuilt; trials read memmap slices, so
  matrix-only ≈ matrix+numba per-trial. The Phase-2 sim exit kernel was **skipped**
  (measurement gate): the post-matrix per-trial residual is bar fetching/slicing
  (`bars_supplier_calls≈5.1M`, `bars_df_slices≈4.1M`), not the numeric bracket
  loop, and `walk_lot_exit` is always called with a live `quote_supplier` +
  `signal_score_fn` in `current_code_parity` (so the callback-free kernel is never
  eligible). See `PHASE_NOTES/walkforward_numba_kernels.md` for the breakdown.

## Rebuild triggers

The on-disk numba cache is keyed by kernel source + numba/llvm versions and
self-busts; just re-run `warm_numba_cache.py` after a kernel change or numba
upgrade. The matrix's own rebuild triggers are unchanged
(`docs/walkforward_scan_matrix_runbook.md`).
