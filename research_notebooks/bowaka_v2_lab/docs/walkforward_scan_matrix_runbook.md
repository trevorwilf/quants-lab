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

`WS=configs/_fastrealism_study.yml`   # fast_realism is now the ONLY matrix family (the IR/_local_container_matrix family is retired)
`STORE=/opt/scan_matrix_cache/fast_realism/validation`   # local-SSD fallback: research_notebooks/bowaka_v2_lab/artifacts/cache/scan_matrix/validation

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
  workers, done ONCE and amortized over all 5000 trials. The validation scope is
  **auto-anchored to the freshest lake session** (3 non-overlapping folds: train 6
  / val 1 / holdout 5 / step 7; tests land ~Oct2024 / May2025 / Dec2025 relative
  to the latest session), so the build size scales with the (now ~2.75 yr /
  ~6.5k-symbol) lake — a multi-hour data job. Run it deliberately, not inside
  CC/CI. (The weekly cron runs it automatically; see "Rebuild triggers" below.)
- **Container-native lake (~10× I/O win).** Inside `ql-jupyter` the lake is the
  persistent native Docker volume `ql_market_data` mounted at
  `/opt/market_data_cache` (survives recreate + `compose down -v`); the config's
  `market_data.shared_root` points at it. The one-time rsync below is only needed
  when first seeding a fresh host:
  ```bash
  # one-time, idempotent (guarded by a .lake_cache_complete marker)
  rsync -a --info=progress2 research_notebooks/market_data/ /opt/market_data_cache/ \
    && touch /opt/market_data_cache/.lake_cache_complete
  # point the config's market_data.shared_root at /opt/market_data_cache (do NOT
  # use MARKET_DATA_ROOT to redirect — it breaks daily split-adjustment resolution).
  ```

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
    --config configs/_fastrealism_study.yml \
    --n-trials 8 --legacy
```

Reports mean per-trial wall-clock, the `phase_seconds` breakdown,
`scanner_symbols_seen` (legacy scan work — collapses to ~0 when the matrix is
active) + `matrix_scans_evaluated` (scans served by the matrix; **0 means it
did NOT fire** — stop and recheck the build/proof), peak RSS, the projected
5000-trial budget, and a `<=3 min/trial` verdict. `--legacy` gives the A/B
speedup ratio vs the disabled scanner.

## 4. Run the fast study

Notebook 10 already points its `CONFIG_PATH` at the fast_realism config
`configs/_fastrealism_study.yml` (resolved with `mode_override=fast_realism`) — it
serves both search and finalist re-score. After the study, read
`artifacts/optuna/<study>__phase_profile.json` for the per-phase + counter breakdown.

### 5000-trial budget

Wall-clock ≈ `5000 × per_trial_seconds / n_jobs` (the fast_realism config sets
`n_jobs: 16`). Pruning trims the doomed tail, so this is an upper bound.

| per-trial | 5000 trials @ n_jobs=16 |
|---|---|
| 1 min | ~5.2 h |
| 2 min | ~10.4 h |
| 3 min | ~15.6 h |

The hard goal is `<=3 min/trial` (so a 5000-trial study is ~1 day);
`benchmark_walkforward_trial.py` prints the measured number + verdict.

---

## Safety contracts (do not violate)

- **Holdout isolation.** The validation-scope matrix EXCLUDES the final-holdout
  window. The fast_realism path sets `separate_holdout_matrix: false` (the FR sweep
  requires this), so BOTH scopes get their own matrix (`…/validation` +
  `…/validation/holdout`); the holdout matrix is read ONLY for the holdout scope
  (`purpose == "final_holdout"`) — never during tuning. The store fails closed on a
  holdout-session read under `purpose != "final_holdout"`.
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

The fast_realism matrix is rebuilt **automatically each week** by
`scheduled_weekly_refresh.ps1` STEP 4 → `rebuild_scan_matrices.ps1` (default =
fast_realism ONLY) on the freshest lake; because the window **auto-anchors** to
the latest session, this fires every week by design. Rebuild MANUALLY (it is
content-addressed by feature/universe/cadence keys, NOT by signals/sizing/exits)
when ANY of these change between weekly runs:

- the lake data (a backfill, a vendor/feed correction, a re-adjustment),
- the feed or simulation mode,
- the scan cadence (`session.scan_interval_seconds`) or scanner window
  (`scanner_start` / `scanner_end`),
- the universe screen (`universe.*`, `historical_features.*`),
- a `MATRIX_SCHEMA_VERSION` bump.

`scan-matrix verify` detects lake drift (the manifest's `dataset_hash` is
re-derived and compared) and flags a stale matrix; rebuild when it does.
