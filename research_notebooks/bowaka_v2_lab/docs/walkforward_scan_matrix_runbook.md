# Walk-forward scan-matrix speedup — operator runbook

How to run a fast notebook-10 walk-forward study on the **scan-matrix
vectorized runtime**: one multi-hour matrix build, amortized over the whole
study, turns each trial's per-symbol feature recompute into a memmap slice +
vectorized gate masks. Everything here is the OPERATOR path; CC ships the
code/config/tests and proves the path on a small build (see
`PHASE_NOTES/optuna_walkforward_scan_matrix_speedup.md`).

All commands run from the lab root with the lab importable:

```bash
cd research_notebooks/bowaka_v2_lab
export PYTHONPATH=src:../bowaka_common/src      # PowerShell: $env:PYTHONPATH="src;../bowaka_common/src"
# use an interpreter with the lab deps (NOT a bare 3.14): e.g. C:/Python312/python.exe
```

`WS=configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml`
`STORE=research_notebooks/bowaka_v2_lab/artifacts/cache/scan_matrix/validation`

---

## 0. Sanity check the wiring (seconds)

```bash
make verify-walkforward-speedup    # or run the pytest files directly (no make)
```
Expect `Walkforward speedup wiring: OK`. This proves the resolver + fail-loud +
overlay + fold-parity + pruning config WITHOUT needing the full build.

## 1. Build the validation-scope matrix (one-time, multi-hour)

```bash
python -m bowaka_v2_lab.cli scan-matrix build \
    --config $WS --scope validation --workers 8 --store-root $STORE
```

- This is the slow step — it is the "one slow scan pass," parallel across
  workers, done ONCE and amortized over all 5000 trials. Measured cost on the
  operator lake: **~98 min for 23 sessions × 3 symbols at 60s cadence**; the
  full validation scope (full PIT universe × all validation sessions) is a
  multi-hour data job. Run it deliberately, not inside CC/CI.
- **Container / 9p lake cache (optional, ~10× I/O win).** Inside `ql-jupyter`
  the lake is a WSL2 9p bind-mount; parallel builds stall in I/O-wait. Mirror
  the lake once to a container-native path and build against it:
  ```bash
  # one-time, idempotent (guarded by a .lake_cache_complete marker)
  rsync -a --info=progress2 research_notebooks/market_data/ /opt/market_data_cache/ \
    && touch /opt/market_data_cache/.lake_cache_complete
  MARKET_DATA_ROOT=... # do NOT use the env var to redirect — it breaks daily
                       # split-adjustment resolution. Instead point the config's
                       # market_data.shared_root at /opt/market_data_cache.
  ```
  On the Windows host / local SSD this is unnecessary (no 9p).

## 2. Verify + write the parity proof (minutes)

```bash
python -m bowaka_v2_lab.cli scan-matrix verify \
    --store-root $STORE --config $WS --vectorized-check
```

- Confirm the printed report `status` is `ok` (or `warn`).
- Confirm `$STORE/parity_proof.json` has `"verifier_version": 2` — the
  vectorized-vs-scalar spot check ran clean. `runtime_mode: vectorized` is
  REFUSED without it (`require_parity_manifest: true`).

## 3. Per-trial sanity check (minutes)

```bash
python scripts/benchmark_walkforward_trial.py \
    --config configs/bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.yml \
    --n-trials 8 --legacy
```

Reports mean per-trial wall-clock, the `phase_seconds` breakdown,
`scanner_symbols_seen` (legacy scan work — collapses to ~0 when the matrix is
active) + `matrix_scans_evaluated` (scans served by the matrix; **0 means it
did NOT fire** — stop and recheck the build/proof), peak RSS, the projected
5000-trial budget, and a `<=3 min/trial` verdict. `--legacy` gives the A/B
speedup ratio vs the disabled scanner.

## 4. Run the fast study

Set notebook 10's `CONFIG_PATH` to the matrix overlay
`configs/bowaka_v2_actual_iex_current_code_optuna.workstation.matrix.yml` and
run. After the study, read `artifacts/optuna/<study>__phase_profile.json` for
the per-phase + counter breakdown.

### 5000-trial budget

Wall-clock ≈ `5000 × per_trial_seconds / n_jobs` (the workstation config sets
`n_jobs: 10`). Pruning trims the doomed tail, so this is an upper bound.

| per-trial | 5000 trials @ n_jobs=10 |
|---|---|
| 1 min | ~8.3 h |
| 2 min | ~16.7 h |
| 3 min | ~25 h |

The hard goal is `<=3 min/trial` (so a 5000-trial study is ~1 day);
`benchmark_walkforward_trial.py` prints the measured number + verdict.

---

## Safety contracts (do not violate)

- **Holdout isolation.** The validation-scope matrix EXCLUDES the final-holdout
  window. `separate_holdout_matrix: true`, and the fold-context builder returns
  the legacy scanner (no matrix) for the holdout scope — never build or read a
  holdout matrix during tuning. The store also fails closed on a holdout-session
  read under `purpose != "final_holdout"`.
- **Search-space safety.** One build serves all 5000 trials because the search
  space tunes only signals / sizing / risk / execution / exits — all
  matrix-invariant. `fail_on_matrix_sensitive_search_space: true` +
  `assert_search_space_compatible_with_matrix` fail closed if a future override
  ever tunes a feature / universe / cadence key.
- **Fail loud, never silent-degrade.** An enabled study with a missing /
  unopenable / unverified matrix raises `OptunaStudyInvalidError` (with the path,
  scope, and these commands). It will NOT fall back to the slow legacy scanner —
  a silent slow run would waste days.
- **Parity is locked.** The matrix runtime is bit/`1e-9`-equivalent to the legacy
  scanner (three-way legacy == compatibility == vectorized parity in
  `tests/parity/test_scan_matrix_vectorized_*`; end-to-end fold parity in
  `tests/integration/test_scan_matrix_walkforward_fold_parity.py`). Never relax a
  tolerance to make a parity check pass — a divergence means the matrix is wrong.

## Rebuild triggers

Rebuild the matrix (it is content-addressed by feature/universe/cadence keys,
NOT by signals/sizing/exits) when ANY of these change:

- the lake data (a backfill, a vendor/feed correction, a re-adjustment),
- the feed or simulation mode,
- the scan cadence (`session.scan_interval_seconds`) or scanner window
  (`scanner_start` / `scanner_end`),
- the universe screen (`universe.*`, `historical_features.*`),
- a `MATRIX_SCHEMA_VERSION` bump.

`scan-matrix verify` detects lake drift (the manifest's `dataset_hash` is
re-derived and compared) and flags a stale matrix; rebuild when it does.
